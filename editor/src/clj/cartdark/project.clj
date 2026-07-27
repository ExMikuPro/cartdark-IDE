;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.project
  "Filesystem-backed CartDark project model."
  (:require [clojure.data.json :as json]
            [clojure.string :as string])
  (:import [java.nio.charset StandardCharsets]
           [java.nio.file Files LinkOption Path Paths]
           [java.util.stream Stream]))

(def ignored-names
  #{".git" ".internal" "build" "__pycache__" ".DS_Store" "Thumbs.db"})

(def supported-text-extensions
  #{"lua" "json" "md" "txt" "c" "h" "py" "cmake"})

(defn ->path ^Path [value]
  (cond
    (instance? Path value) value
    (string? value) (Paths/get ^String value (make-array String 0))
    :else (throw (ex-info "Expected a filesystem path" {:value value}))))

(defn pack-path
  "Resolves either a project directory or a pack.json selection."
  ^Path [selection]
  (let [path (.toAbsolutePath (.normalize (->path selection)))]
    (if (and (Files/isRegularFile path (make-array LinkOption 0))
             (= "pack.json" (str (.getFileName path))))
      path
      (.resolve path "pack.json"))))

(defn ignored-path? [^Path path]
  (let [name (str (.getFileName path))]
    (or (contains? ignored-names name)
        (string/starts-with? name "."))))

(defn scan-files
  "Returns sorted project-relative paths without generated or hidden directories."
  [root]
  (let [root (.toAbsolutePath (.normalize (->path root)))]
    (with-open [^Stream paths (Files/walk root (make-array java.nio.file.FileVisitOption 0))]
      (->> (.iterator paths)
           iterator-seq
           (remove #(= root %))
           (remove (fn [^Path path]
                     (some ignored-path? (iterator-seq (.iterator (.relativize root path))))))
           (map #(str (.relativize root ^Path %)))
           sort
           vec))))

(defn read-pack
  "Reads and validates the minimum CartDark pack.json contract."
  [selection]
  (let [pack (pack-path selection)
        root (.getParent pack)]
    (when-not (Files/isDirectory root (make-array LinkOption 0))
      (throw (ex-info "Project directory does not exist"
                      {:type :project-directory-missing :path (str root)})))
    (when-not (Files/isRegularFile pack (make-array LinkOption 0))
      (throw (ex-info "pack.json does not exist"
                      {:type :pack-missing :path (str pack)})))
    (let [text (try
                 (Files/readString pack StandardCharsets/UTF_8)
                 (catch Exception cause
                   (throw (ex-info "pack.json is not valid UTF-8"
                                   {:type :pack-encoding :path (str pack)}
                                   cause))))
          data (try
                 (json/read-str text :key-fn keyword)
                 (catch Exception cause
                   (throw (ex-info "pack.json is not valid JSON"
                                   {:type :pack-json :path (str pack)}
                                   cause))))]
      (when-not (map? data)
        (throw (ex-info "pack.json top level must be an object"
                        {:type :pack-shape :path (str pack)})))
      (when-not (= "XHGC_PACK" (:format data))
        (throw (ex-info "pack.json format must be XHGC_PACK"
                        {:type :pack-format :actual (:format data) :path (str pack)})))
      (let [meta (or (:meta data) {})
            directory-name (str (.getFileName root))]
        {:root-path (str root)
         :pack-path (str pack)
         :name (or (not-empty (:title meta)) directory-name)
         :entry (:entry meta)
         :meta meta
         :files (scan-files root)
         :dirty-files #{}
         :pack data}))))

(defn valid-project? [selection]
  (try
    (read-pack selection)
    true
    (catch Exception _
      false)))

(defn relative-path ^String [project path]
  (let [root (->path (:root-path project))
        absolute (.toAbsolutePath (.normalize (->path path)))]
    (str (.relativize root absolute))))

(defn text-file? [path]
  (let [name (string/lower-case (str (.getFileName (->path path))))
        index (.lastIndexOf name ".")
        extension (if (neg? index) name (subs name (inc index)))]
    (contains? supported-text-extensions extension)))
