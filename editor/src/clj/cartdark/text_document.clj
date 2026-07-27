;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.text-document
  "Pure, filesystem-backed text document state used by the native code view."
  (:require [cartdark.project :as project]
            [editor.code.data :as code-data])
  (:import [java.nio.charset StandardCharsets]
           [java.nio.file Files LinkOption Path StandardOpenOption]))

(defn load-document [path]
  (let [path (.toAbsolutePath (.normalize (project/->path path)))]
    (when-not (Files/isRegularFile path (make-array LinkOption 0))
      (throw (ex-info "File does not exist" {:type :file-missing :path (str path)})))
    (let [text (try
                 (Files/readString path StandardCharsets/UTF_8)
                 (catch Exception cause
                   (throw (ex-info "File is not valid UTF-8"
                                   {:type :file-encoding :path (str path)}
                                   cause))))]
      {:path path
       :disk-text text
       :text text
       :lines (code-data/string->lines text)
       :undo []
       :redo []
       :disk-modified-at (Files/getLastModifiedTime path (make-array LinkOption 0))})))

(defn dirty? [document]
  (not= (:disk-text document) (:text document)))

(defn replace-text [document text]
  (if (= text (:text document))
    document
    (-> document
        (update :undo conj (:text document))
        (assoc :text text
               :lines (code-data/string->lines text)
               :redo []))))

(defn replace-lines [document lines]
  (replace-text document (code-data/lines->string lines)))

(defn undo [document]
  (if-let [text (peek (:undo document))]
    (-> document
        (update :undo pop)
        (update :redo conj (:text document))
        (assoc :text text :lines (code-data/string->lines text)))
    document))

(defn redo [document]
  (if-let [text (peek (:redo document))]
    (-> document
        (update :redo pop)
        (update :undo conj (:text document))
        (assoc :text text :lines (code-data/string->lines text)))
    document))

(defn save! [document]
  (let [^Path path (:path document)]
    (Files/writeString path (:text document) StandardCharsets/UTF_8
                       (into-array java.nio.file.OpenOption
                                   [StandardOpenOption/CREATE
                                    StandardOpenOption/TRUNCATE_EXISTING
                                    StandardOpenOption/WRITE]))
    (assoc document
           :disk-text (:text document)
           :disk-modified-at (Files/getLastModifiedTime path (make-array LinkOption 0)))))

(defn externally-modified? [document]
  (let [^Path path (:path document)]
    (or (not (Files/exists path (make-array LinkOption 0)))
        (not= (:disk-modified-at document)
              (Files/getLastModifiedTime path (make-array LinkOption 0))))))

(defn close-action
  "Returns :close, :save-and-close or :cancel for a requested close decision."
  [document decision]
  (if-not (dirty? document)
    :close
    (case decision
      :save :save-and-close
      :discard :close
      :cancel :cancel
      :cancel)))
