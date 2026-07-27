;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.preferences-test
  (:require [cartdark.preferences :as preferences]
            [clojure.test :refer :all])
  (:import [java.nio.file Files]))

(deftest persists-recent-projects
  (let [dir (Files/createTempDirectory "cartdark-prefs-test"
                                       (make-array java.nio.file.attribute.FileAttribute 0))
        path (.resolve dir "settings.json")
        settings (-> preferences/defaults
                     (preferences/add-recent "/projects/one")
                     (preferences/add-recent "/projects/two"))]
    (preferences/save! path settings)
    (let [loaded (preferences/load! path)]
      (is (= ["/projects/two" "/projects/one"] (:recent-projects loaded)))
      (is (= "/projects/two" (:last-project loaded))))))
