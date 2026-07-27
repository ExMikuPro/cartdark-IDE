;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.text-document-test
  (:require [cartdark.text-document :as document]
            [clojure.test :refer :all])
  (:import [java.nio.charset StandardCharsets]
           [java.nio.file Files]))

(deftest reads-saves-and-tracks-utf8-lua
  (let [path (Files/createTempFile "cartdark-document" ".lua"
                                   (make-array java.nio.file.attribute.FileAttribute 0))]
    (Files/writeString path "local 标题 = \"你好\"\n" StandardCharsets/UTF_8
                       (make-array java.nio.file.OpenOption 0))
    (let [loaded (document/load-document path)
          edited (document/replace-text loaded "local 标题 = \"CartDark\"\n")]
      (is (= "local 标题 = \"你好\"\n" (:text loaded)))
      (is (false? (document/dirty? loaded)))
      (is (true? (document/dirty? edited)))
      (is (= :cancel (document/close-action edited :cancel)))
      (is (= :save-and-close (document/close-action edited :save)))
      (let [saved (document/save! edited)]
        (is (false? (document/dirty? saved)))
        (is (= "local 标题 = \"CartDark\"\n"
               (Files/readString path StandardCharsets/UTF_8)))))))

(deftest undo-and-redo
  (let [path (Files/createTempFile "cartdark-undo" ".txt"
                                   (make-array java.nio.file.attribute.FileAttribute 0))]
    (Files/writeString path "one" StandardCharsets/UTF_8
                       (make-array java.nio.file.OpenOption 0))
    (let [loaded (document/load-document path)
          edited (document/replace-text loaded "two")]
      (is (= "one" (:text (document/undo edited))))
      (is (= "two" (:text (-> edited document/undo document/redo)))))))
