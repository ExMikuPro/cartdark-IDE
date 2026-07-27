;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.project-tree
  "Mutation and watch helpers for ordinary project files."
  (:require [cartdark.project :as project])
  (:import [java.nio.charset StandardCharsets]
           [java.nio.file Files LinkOption Path StandardCopyOption StandardWatchEventKinds WatchService]))

(defn- inside-root! ^Path [root path]
  (let [root (.toAbsolutePath (.normalize (project/->path root)))
        path (.toAbsolutePath (.normalize (project/->path path)))]
    (when-not (.startsWith path root)
      (throw (ex-info "Path is outside the project root" {:root (str root) :path (str path)})))
    path))

(defn create-directory! [root path]
  (Files/createDirectories (inside-root! root path) (make-array java.nio.file.attribute.FileAttribute 0)))

(defn create-lua-file! [root path]
  (let [path (inside-root! root path)]
    (Files/createDirectories (.getParent path) (make-array java.nio.file.attribute.FileAttribute 0))
    (Files/writeString path "-- CartDark Studio\n" StandardCharsets/UTF_8
                       (into-array java.nio.file.OpenOption
                                   [java.nio.file.StandardOpenOption/CREATE_NEW]))
    path))

(defn rename! [root from to]
  (Files/move (inside-root! root from)
              (inside-root! root to)
              (into-array java.nio.file.CopyOption [StandardCopyOption/ATOMIC_MOVE])))

(defn delete! [root path]
  (let [path (inside-root! root path)]
    (when (Files/isDirectory path (make-array LinkOption 0))
      (with-open [paths (Files/walk path (make-array java.nio.file.FileVisitOption 0))]
        (doseq [child (reverse (sort-by #(.getNameCount ^Path %) (iterator-seq (.iterator paths))))]
          (Files/deleteIfExists child))))
    (Files/deleteIfExists path)))

(defn watch-service ^WatchService [root]
  (let [root (project/->path root)
        watcher (.newWatchService (.getFileSystem root))]
    (.register root watcher
               (into-array java.nio.file.WatchEvent$Kind
                           [StandardWatchEventKinds/ENTRY_CREATE
                            StandardWatchEventKinds/ENTRY_DELETE
                            StandardWatchEventKinds/ENTRY_MODIFY]))
    watcher))
