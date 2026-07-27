;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.project-test
  (:require [cartdark.project :as project]
            [clojure.test :refer :all])
  (:import [java.nio.charset StandardCharsets]
           [java.nio.file Files Path]))

(defn- temp-project []
  (Files/createTempDirectory "cartdark-project-test"
                             (make-array java.nio.file.attribute.FileAttribute 0)))

(defn- write! [^Path root relative text]
  (let [path (.resolve root relative)]
    (Files/createDirectories (.getParent path)
                             (make-array java.nio.file.attribute.FileAttribute 0))
    (Files/writeString path text StandardCharsets/UTF_8
                       (make-array java.nio.file.OpenOption 0))
    path))

(deftest opens-valid-pack-json
  (let [root (temp-project)
        pack (write! root "pack.json"
                     "{\"format\":\"XHGC_PACK\",\"meta\":{\"title\":\"Demo\",\"entry\":\"app/main.lua\"}}")
        loaded (project/read-pack pack)]
    (is (= "Demo" (:name loaded)))
    (is (= "app/main.lua" (:entry loaded)))
    (is (= (str pack) (:pack-path loaded)))))

(deftest rejects-invalid-pack-json
  (let [root (temp-project)]
    (write! root "pack.json" "{\"format\":\"NOT_CARTDARK\"}")
    (is (thrown-with-msg? clojure.lang.ExceptionInfo
                          #"format must be XHGC_PACK"
                          (project/read-pack root)))))

(deftest scans-project-and-ignores-generated-and-hidden-directories
  (let [root (temp-project)]
    (write! root "pack.json" "{\"format\":\"XHGC_PACK\"}")
    (write! root "app/main.lua" "return true")
    (write! root ".git/config" "ignored")
    (write! root ".hidden/secret.lua" "ignored")
    (write! root "build/cart.bin" "ignored")
    (write! root "assets/readme.txt" "visible")
    (is (= ["app" "app/main.lua" "assets" "assets/readme.txt" "pack.json"]
           (project/scan-files root)))))
