;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.build-test
  (:require [cartdark.build :as build]
            [cartdark.process :as process]
            [clojure.test :refer :all])
  (:import [java.nio.file Files]))

(deftest parses-json-build-errors
  (is (= {:kind :json
          :value {:severity "error"
                  :message "bad lua"
                  :file "app/main.lua"
                  :line 4
                  :column 2
                  :step "compile"}}
         (build/parse-log-line
           "{\"severity\":\"error\",\"message\":\"bad lua\",\"file\":\"app/main.lua\",\"line\":4,\"column\":2,\"step\":\"compile\"}"))))

(deftest preserves-non-json-output
  (is (= {:kind :console :text "Building entry chunk"}
         (build/parse-log-line "Building entry chunk"))))

(deftest handles-process-exit-code-and-streams
  (let [lines (atom [])
        result (process/run! {:command ["sh" "-c" "printf 'ok\\n'; printf 'bad\\n' >&2; exit 7"]
                              :on-line #(swap! lines conj [%1 %2])})]
    (is (= 7 (:exit-code result)))
    (is (some #{[:stdout "ok"]} @lines))
    (is (some #{[:stderr "bad"]} @lines))))

(deftest finds-configured-tool-and-adapts-python-cli
  (let [root (Files/createTempDirectory "xhgc-pack-test"
                                        (make-array java.nio.file.attribute.FileAttribute 0))
        script (.resolve root "main.py")]
    (Files/writeString script "print('test')" (make-array java.nio.file.OpenOption 0))
    (is (= script (build/resolve-tool {:configured-path root :environment {}})))
    (is (= ["python3" (str script) "pack.json" "build/cart.bin"]
           (build/command script "pack.json" "build/cart.bin")))))
