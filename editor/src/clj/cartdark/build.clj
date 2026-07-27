;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.build
  "xhgc-pack discovery, command adaptation, streaming logs, and build lifecycle."
  (:require [cartdark.process :as process]
            [cartdark.project :as project]
            [clojure.data.json :as json]
            [clojure.string :as string])
  (:import [java.nio.file Files LinkOption Path Paths]
           [java.util UUID]))

(defn- executable? [^Path path]
  (and (Files/isRegularFile path (make-array LinkOption 0))
       (or (Files/isExecutable path)
           (= "main.py" (str (.getFileName path))))))

(defn- path-executable [name]
  (some (fn [directory]
          (let [candidate (.resolve (project/->path directory) name)]
            (when (executable? candidate) candidate)))
        (remove string/blank?
                (string/split (or (System/getenv "PATH") "")
                              (re-pattern (java.io.File/pathSeparator))))))

(defn install-root ^Path []
  (if-let [configured (System/getProperty "cartdark.install.dir")]
    (.toAbsolutePath (.normalize (project/->path configured)))
    (let [cwd (.toAbsolutePath (.normalize (project/->path (System/getProperty "user.dir"))))]
      (if (= "editor" (str (.getFileName cwd))) (.getParent cwd) cwd))))

(defn- directory-tool [^Path path]
  (cond
    (executable? (.resolve path "xhgc-pack")) (.resolve path "xhgc-pack")
    (Files/isRegularFile (.resolve path "main.py") (make-array LinkOption 0)) (.resolve path "main.py")
    :else nil))

(defn resolve-tool
  "Finds xhgc-pack in the documented priority order."
  [{:keys [configured-path environment]
    :or {environment (System/getenv)}}]
  (let [root (install-root)
        candidates [(some-> configured-path project/->path)
                    (some-> (get environment "XHGC_PACK") project/->path)
                    (path-executable "xhgc-pack")
                    (.resolve root "tools/xhgc-pack")
                    (.resolve (.getParent root) "xhgc-pack")]]
    (some (fn [candidate]
            (when candidate
              (let [absolute (.toAbsolutePath (.normalize ^Path candidate))]
                (cond
                  (executable? absolute) absolute
                  (Files/isDirectory absolute (make-array LinkOption 0)) (directory-tool absolute)))))
          candidates)))

(defn command
  "Adapts to the currently deployed xhgc-pack CLI. The adjacent source checkout
  exposes main.py PACK_JSON OUTPUT, while installed binaries receive the same
  two positional arguments."
  [tool pack output]
  (let [tool (project/->path tool)]
    (if (= "main.py" (str (.getFileName tool)))
      [(or (System/getenv "PYTHON") "python3") (str tool) (str pack) (str output)]
      [(str tool) (str pack) (str output)])))

(def build-error-fields [:severity :message :file :line :column :step])

(defn parse-log-line [line]
  (try
    (let [value (json/read-str line :key-fn keyword)]
      (if (map? value)
        {:kind :json
         :value (merge (zipmap build-error-fields (repeat nil))
                       (select-keys value build-error-fields))}
        {:kind :console :text line}))
    (catch Exception _
      {:kind :console :text line})))

(defn start-build!
  [{:keys [project configured-path rebuild? on-console on-error on-complete]
    :or {on-console (fn [_])
         on-error (fn [_])
         on-complete (fn [_])}}]
  (let [tool (resolve-tool {:configured-path configured-path})]
    (when-not tool
      (throw (ex-info "xhgc-pack was not found. Configure it in CartDark Studio settings or set XHGC_PACK."
                      {:type :xhgc-pack-not-found})))
    (let [root (project/->path (:root-path project))
          pack (project/->path (:pack-path project))
          build-dir (.resolve root "build")
          output (.resolve build-dir "cart.bin")]
      (Files/createDirectories build-dir (make-array java.nio.file.attribute.FileAttribute 0))
      (when (and rebuild? (Files/exists output (make-array LinkOption 0)))
        (Files/delete output))
      (process/start!
        {:command (command tool pack output)
         :directory (.getParent tool)
         :on-line (fn [stream line]
                    (let [parsed (parse-log-line line)]
                      (if (= :json (:kind parsed))
                        (on-error (:value parsed))
                        (on-console {:stream stream :text (:text parsed)}))))
         :on-exit (fn [exit-code]
                    (on-complete {:exit-code exit-code
                                  :success? (zero? exit-code)
                                  :output (str output)}))}))))
