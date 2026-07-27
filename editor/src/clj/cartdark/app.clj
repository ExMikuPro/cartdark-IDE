;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.app
  "CartDark Studio's JavaFX/cljfx main window and editor orchestration."
  (:require [cartdark.build :as build]
            [cartdark.lua :as cartdark-lua]
            [cartdark.preferences :as preferences]
            [cartdark.project :as project]
            [cartdark.simulator :as simulator]
            [cartdark.text-document :as document]
            [cartdark.text-resource :as text-resource]
            [cljfx.api :as fx]
            [clojure.string :as string]
            [dynamo.graph :as g]
            [editor.code.data :as code-data]
            [editor.code.lang.cish :as cish]
            [editor.code.lang.json :as json-language]
            [editor.code.view :as code-view]
            [editor.prefs :as editor-prefs])
  (:import [java.nio.file Files LinkOption Path]
           [javafx.application Platform]
           [javafx.beans.property SimpleStringProperty]
           [javafx.event EventHandler]
           [javafx.fxml FXMLLoader]
           [javafx.scene Parent Scene]
           [javafx.scene.control Alert Alert$AlertType ButtonType ContextMenu Label ListView MenuItem
            ProgressBar Tab TabPane TableColumn TableView TreeCell TreeItem TreeView]
           [javafx.scene.input Clipboard ClipboardContent MouseButton MouseEvent]
           [javafx.scene.layout AnchorPane GridPane Pane VBox]
           [javafx.stage DirectoryChooser FileChooser Stage]))

(defonce ^:private state
  (atom {:stage nil
         :root nil
         :project nil
         :documents {}
         :closed-files []
         :settings (preferences/load!)
         :properties-component nil
         :active-build nil}))

(defn- lookup [root id]
  (or (get (:controls @state) id)
      (.lookup ^Parent root (str "#" id))))

(defn- ui! [f]
  (if (Platform/isFxApplicationThread) (f) (Platform/runLater f)))

(defn- show-error! [title message]
  (doto (Alert. Alert$AlertType/ERROR message (into-array ButtonType [ButtonType/OK]))
    (.setTitle title)
    (.setHeaderText nil)
    (.showAndWait)))

(defn- console! [text]
  (ui! #(let [^ListView list (lookup (:root @state) "console-list")]
          (.add (.getItems list) (str text))
          (.scrollTo list (dec (.size (.getItems list)))))))

(defn- status! [text]
  (ui! #(.setText ^Label (lookup (:root @state) "status-label") (str text))))

(defn- grammar-for [^Path path]
  (let [name (.toLowerCase (str (.getFileName path)))]
    (cond
      (.endsWith name ".lua") cartdark-lua/grammar
      (.endsWith name ".json") json-language/grammar
      (or (.endsWith name ".c") (.endsWith name ".h")) cish/grammar
      :else nil)))

(defn- display-path [^Path path]
  (str (.getFileName path)))

(defn- dirty-title [^Path path dirty?]
  (str (display-path path) (when dirty? " ●")))

(defn- selected-tab []
  (some-> ^TabPane (lookup (:root @state) "editor-tabs")
          .getSelectionModel
          .getSelectedItem))

(defn- entry-for-tab [^Tab tab]
  (some (fn [[_ entry]] (when (identical? tab (:tab entry)) entry))
        (:documents @state)))

(defn- save-entry! [{:keys [path document resource-node tab]}]
  (try
    (let [lines (g/node-value resource-node :modified-lines)
          saved (-> @document
                    (document/replace-lines lines)
                    document/save!)]
      (reset! document saved)
      (text-resource/mark-saved! resource-node)
      (.setText ^Tab tab (dirty-title path false))
      (status! (str "Saved " path))
      true)
    (catch Exception cause
      (show-error! "Save failed" (.getMessage cause))
      false)))

(defn save-current! []
  (when-let [entry (some-> (selected-tab) entry-for-tab)]
    (save-entry! entry)))

(defn save-all! []
  (every? true? (map save-entry! (vals (:documents @state)))))

(defn- confirm-close! [entry]
  (if-not (document/dirty? @(:document entry))
    true
    (let [save-button (ButtonType. "Save")
          discard-button (ButtonType. "Discard")
          alert (Alert. Alert$AlertType/CONFIRMATION
                        (str "Save changes to " (:path entry) "?")
                        (into-array ButtonType [save-button discard-button ButtonType/CANCEL]))
          result (.orElse (.showAndWait alert) ButtonType/CANCEL)]
      (cond
        (= result save-button) (save-entry! entry)
        (= result discard-button) true
        :else false))))

(defn- close-entry! [entry]
  (when (confirm-close! entry)
    ((:dispose! (:native entry)))
    (g/delete-node! (:resource-node entry))
    (swap! state
           (fn [s]
             (-> s
                 (update :documents dissoc (:path entry))
                 (update :closed-files #(vec (take 20 (cons (:path entry) %)))))))
    true))

(defn- clipboard! [text]
  (let [content (doto (ClipboardContent.) (.putString (str text)))]
    (.setContent (Clipboard/getSystemClipboard) content)))

(defn- tab-context-menu [entry]
  (let [menu (ContextMenu.)
        save (MenuItem. "Save")
        close-others (MenuItem. "Close Others")
        close-right (MenuItem. "Close to the Right")
        copy-path (MenuItem. "Copy Path")
        ^TabPane tabs (lookup (:root @state) "editor-tabs")]
    (.setOnAction save (reify EventHandler (handle [_ _] (save-entry! entry))))
    (.setOnAction
      close-others
      (reify EventHandler
        (handle [_ _]
          (doseq [^Tab tab (vec (.getTabs tabs))
                  :when (not (identical? tab (:tab entry)))]
            (when-let [other (entry-for-tab tab)]
              (when (close-entry! other) (.remove (.getTabs tabs) tab)))))))
    (.setOnAction
      close-right
      (reify EventHandler
        (handle [_ _]
          (let [index (.indexOf (.getTabs tabs) (:tab entry))]
            (doseq [^Tab tab (vec (drop (inc index) (.getTabs tabs)))]
              (when-let [other (entry-for-tab tab)]
                (when (close-entry! other) (.remove (.getTabs tabs) tab))))))))
    (.setOnAction copy-path (reify EventHandler (handle [_ _] (clipboard! (:path entry)))))
    (.addAll (.getItems menu) (into-array MenuItem [save close-others close-right copy-path]))
    menu))

(defn- render-properties! [^Path path]
  (when-let [component (:properties-component @state)]
    (fx/delete-component component))
  (let [project (:project @state)
        relative (when (and project path) (project/relative-path project path))
        component
        (fx/create-component
          {:fx/type :v-box
           :spacing 8
           :style-class ["properties-grid"]
           :children
           [{:fx/type :label :text (if path (display-path path) "No selection")}
            {:fx/type :label :text (or relative "")}
            {:fx/type :label :text (if path (str path) "")}]})]
    (let [^GridPane grid (lookup (:root @state) "properties-grid")]
      (.clear (.getChildren grid))
      (.add (.getChildren grid) (fx/instance component)))
    (swap! state assoc :properties-component component)))

(defn- open-file! [path]
  (let [path (.toAbsolutePath (.normalize (project/->path path)))
        existing (get-in @state [:documents path])
        ^TabPane tabs (lookup (:root @state) "editor-tabs")]
    (cond
      existing
      (.select (.getSelectionModel tabs) ^Tab (:tab existing))

      (not (project/text-file? path))
      (status! (str "Unsupported text file: " path))

      :else
      (try
        (let [doc (atom (document/load-document path))
              graph (g/make-graph! :history true :volatility 2)
              resource-node (text-resource/make! graph path (:lines @doc))
              host (AnchorPane.)
              tab (Tab. (dirty-title path false) host)
              native (code-view/make-standalone-view!
                       graph host resource-node (grammar-for path)
                       (:code-prefs @state)
                       (fn [lines]
                         (swap! doc document/replace-lines lines)
                         (ui! #(.setText tab (dirty-title path (document/dirty? @doc))))))
              entry {:path path :document doc :graph graph :resource-node resource-node
                     :native native :tab tab}]
          (AnchorPane/setTopAnchor host 0.0)
          (.setContextMenu tab (tab-context-menu entry))
          (.setOnCloseRequest
            tab
            (reify EventHandler
              (handle [_ event]
                (when-not (close-entry! entry)
                  (.consume event)))))
          (.add (.getTabs tabs) tab)
          (swap! state assoc-in [:documents path] entry)
          (.select (.getSelectionModel tabs) tab)
          (render-properties! path))
        (catch Exception cause
          (show-error! "Open file failed" (.getMessage cause)))))))

(defn- tree-item [^Path path]
  (let [item (TreeItem. path)]
    (when (Files/isDirectory path (make-array LinkOption 0))
      (with-open [children (Files/list path)]
        (doseq [child (->> (iterator-seq (.iterator children))
                           (remove project/ignored-path?)
                           (sort-by #(str (.getFileName ^Path %))))]
          (.add (.getChildren item) (tree-item child)))))
    item))

(defn- refresh-tree! []
  (when-let [project (:project @state)]
    (let [root-path (project/->path (:root-path project))
          ^TreeView tree (lookup (:root @state) "project-tree")
          item (tree-item root-path)]
      (.setExpanded item true)
      (.setRoot tree item))))

(defn- set-project! [selection]
  (try
    (let [loaded (project/read-pack selection)
          settings (-> (:settings @state)
                       (preferences/add-recent (:root-path loaded)))]
      (preferences/save! settings)
      (swap! state assoc :project loaded :settings settings)
      (.setTitle ^Stage (:stage @state) (str "CartDark Studio — " (:name loaded)))
      (.setText ^Label (lookup (:root @state) "project-status-label") (:name loaded))
      (refresh-tree!)
      (status! (str "Opened " (:pack-path loaded)))
      loaded)
    (catch Exception cause
      (show-error! "Invalid CartDark project" (.getMessage cause))
      nil)))

(defn- choose-project! []
  (let [chooser (DirectoryChooser.)]
    (.setTitle chooser "Open CartDark Project")
    (when-let [directory (.showDialog chooser ^Stage (:stage @state))]
      (set-project! (.toPath directory)))))

(defn- add-build-error! [error]
  (ui!
    #(let [^TableView table (lookup (:root @state) "build-errors-table")]
       (.add (.getItems table) error))))

(defn- configure-build-table! []
  (let [^TableView table (lookup (:root @state) "build-errors-table")]
    (doseq [[^TableColumn column field] (map vector (.getColumns table)
                                             [:severity :message :file :line :column :step])]
      (.setCellValueFactory
        column
        (reify javafx.util.Callback
          (call [_ features]
            (SimpleStringProperty.
              (str (or (get (.getValue features) field) "")))))))))

(defn- build! [rebuild? run-after?]
  (if-not (:project @state)
    (show-error! "No project" "Open a directory containing pack.json first.")
    (when (save-all!)
      (let [^TableView errors (lookup (:root @state) "build-errors-table")
            ^ProgressBar progress (lookup (:root @state) "progress-bar")]
        (.clear (.getItems errors))
        (.setVisible progress true)
        (.setProgress progress ProgressBar/INDETERMINATE_PROGRESS)
        (status! "Building cart.bin…")
        (try
          (let [settings (:settings @state)
                handle
                (build/start-build!
                  {:project (:project @state)
                   :configured-path (:xhgc-pack-path settings)
                   :rebuild? rebuild?
                   :on-console #(console! (str (name (:stream %)) ": " (:text %)))
                   :on-error add-build-error!
                   :on-complete
                   (fn [{:keys [success? exit-code output]}]
                     (ui!
                       #(do
                          (.setVisible progress false)
                          (status! (if success?
                                     (str "Build succeeded: " output)
                                     (str "Build failed with exit code " exit-code)))))
                     (when (and success? run-after?)
                       (if-let [tool (simulator/resolve-simulator
                                      {:configured-path (:simulator-path settings)
                                       :install-root (build/install-root)})]
                         (simulator/start! tool output
                                           (fn [stream line]
                                             (console! (str (name stream) ": " line)))
                                           #(console! (str "Simulator exited with code " %)))
                         (console! "Build succeeded, but cartdesk-simulator was not found."))))})]
            (swap! state assoc :active-build handle))
          (catch Exception cause
            (.setVisible progress false)
            (status! "Build could not start")
            (show-error! "Build failed" (.getMessage cause))))))))

(defn- reopen-closed! []
  (when-let [path (first (:closed-files @state))]
    (swap! state update :closed-files #(vec (rest %)))
    (open-file! path)))

(defn- wire-actions! []
  (let [root (:root @state)
        handler (fn [f] (reify EventHandler (handle [_ _] (f))))]
    (.setOnAction ^MenuItem (lookup root "open-project-menu") (handler choose-project!))
    (.setOnAction ^MenuItem (lookup root "save-menu") (handler save-current!))
    (.setOnAction ^MenuItem (lookup root "save-all-menu") (handler save-all!))
    (.setOnAction ^MenuItem (lookup root "reopen-menu") (handler reopen-closed!))
    (.setOnAction ^MenuItem (lookup root "refresh-menu") (handler refresh-tree!))
    (.setOnAction ^MenuItem (lookup root "build-menu") (handler #(build! false false)))
    (.setOnAction ^MenuItem (lookup root "rebuild-menu") (handler #(build! true false)))
    (.setOnAction ^MenuItem (lookup root "run-menu") (handler #(build! false true)))))

(defn- configure-tree! []
  (let [^TreeView tree (lookup (:root @state) "project-tree")]
    (.setCellFactory
      tree
      (reify javafx.util.Callback
        (call [_ _]
          (proxy [TreeCell] []
            (updateItem [item empty?]
              (proxy-super updateItem item empty?)
              (.setText this
                        (when-not empty?
                          (display-path ^Path item))))))))
    (.setOnMouseClicked
      tree
      (reify EventHandler
        (handle [_ event]
          (let [^MouseEvent event event]
            (when-let [^TreeItem selected (.getSelectedItem (.getSelectionModel tree))]
              (let [^Path path (.getValue selected)]
              (render-properties! path)
              (when (and (= MouseButton/PRIMARY (.getButton event))
                         (= 2 (.getClickCount event))
                         (Files/isRegularFile path (make-array LinkOption 0)))
                  (open-file! path))))))))))

(defn open-project!
  "Creates the CartDark main window and optionally opens a project directory or pack.json."
  [selection]
  (let [loader (FXMLLoader. (clojure.java.io/resource "cartdark-studio.fxml"))
        root (.load loader)
        stage (Stage.)
        prefs-file (.resolve (preferences/settings-dir) "code-editor-prefs.edn")]
    (Files/createDirectories (.getParent prefs-file)
                             (make-array java.nio.file.attribute.FileAttribute 0))
    (swap! state assoc
           :root root
           :stage stage
           :controls (into {} (map (fn [[key value]]
                                     [(string/replace (str key) "_" "-") value])
                                   (.getNamespace loader)))
           :code-prefs (editor-prefs/global prefs-file))
    (code-view/initialize! (:code-prefs @state))
    (.setTitle stage "CartDark Studio")
    (.setScene stage (Scene. root 1240.0 800.0))
    (configure-build-table!)
    (configure-tree!)
    (wire-actions!)
    (.setOnCloseRequest
      stage
      (reify EventHandler
        (handle [_ event]
          (when-not (every? confirm-close! (vals (:documents @state)))
            (.consume event)))))
    (.show stage)
    (when selection
      (set-project! selection))
    stage))
