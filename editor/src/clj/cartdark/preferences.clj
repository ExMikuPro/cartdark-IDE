;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.preferences
  "CartDark-specific settings location and JSON persistence."
  (:require [clojure.data.json :as json]
            [clojure.string :as string])
  (:import [java.nio.charset StandardCharsets]
           [java.nio.file Files Path Paths StandardCopyOption StandardOpenOption]))

(def defaults
  {:recent-projects []
   :last-project nil
   :window {:x nil :y nil :width 1200.0 :height 800.0}
   :panels {:left 0.22 :right 0.78 :bottom 0.70}
   :open-files []
   :active-tab nil
   :theme "dark"
   :font "Dejavu Sans Mono"
   :font-size 13.0
   :xhgc-pack-path nil
   :simulator-path nil})

(defn settings-dir ^Path []
  (let [os (string/lower-case (System/getProperty "os.name"))
        user-home (System/getProperty "user.home")]
    (cond
      (string/includes? os "mac")
      (Paths/get user-home (into-array String ["Library" "Application Support" "CartDark Studio"]))

      (string/includes? os "win")
      (Paths/get (or (System/getenv "APPDATA")
                     (str user-home "\\AppData\\Roaming"))
                 (into-array String ["CartDark Studio"]))

      :else
      (Paths/get (or (System/getenv "XDG_CONFIG_HOME")
                     (str user-home "/.config"))
                 (into-array String ["cartdark-studio"])))))

(defn settings-path ^Path []
  (.resolve (settings-dir) "settings.json"))

(defn load!
  ([] (load! (settings-path)))
  ([^Path path]
   (if-not (Files/isRegularFile path (make-array java.nio.file.LinkOption 0))
     defaults
     (try
       (merge defaults
              (json/read-str (Files/readString path StandardCharsets/UTF_8)
                             :key-fn keyword))
       (catch Exception _
         defaults)))))

(defn save!
  ([settings] (save! (settings-path) settings))
  ([^Path path settings]
   (Files/createDirectories (.getParent path) (make-array java.nio.file.attribute.FileAttribute 0))
   (let [temporary (.resolveSibling path (str (.getFileName path) ".tmp"))]
     (Files/writeString temporary (json/write-str settings) StandardCharsets/UTF_8
                        (into-array java.nio.file.OpenOption
                                    [StandardOpenOption/CREATE
                                     StandardOpenOption/TRUNCATE_EXISTING
                                     StandardOpenOption/WRITE]))
     (Files/move temporary path
                 (into-array java.nio.file.CopyOption
                             [StandardCopyOption/REPLACE_EXISTING
                              StandardCopyOption/ATOMIC_MOVE])))
   settings))

(defn add-recent [settings project-path]
  (assoc settings
         :last-project project-path
         :recent-projects (->> (cons project-path (:recent-projects settings))
                               distinct
                               (take 12)
                               vec)))
