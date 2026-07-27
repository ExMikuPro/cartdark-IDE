;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.lua-api-test
  (:require [cartdark.lua-api :as lua-api]
            [clojure.test :refer :all]))

(deftest loads-cartdark-api-and-warns-about-firmware-unsupported-modules
  (let [api (lua-api/load-api)]
    (is (= "CartDark firmware" (:environment api)))
    (is (some #(= "update" (:name %)) (:lifecycle api)))
    (is (= :warning (:severity (lua-api/warning-for "io"))))
    (is (nil? (lua-api/warning-for "ui")))))
