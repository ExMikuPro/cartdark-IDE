;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.lua-api
  "Loader and warning interface for CartDark firmware Lua API metadata."
  (:require [clojure.data.json :as json]
            [clojure.java.io :as io]))

(def resource-name "cartdark/lua/cartdark_api.json")

(defn load-api []
  (with-open [reader (io/reader (io/resource resource-name) :encoding "UTF-8")]
    (json/read reader :key-fn keyword)))

(defn unavailable-modules []
  (into #{} (map :name) (:unavailable_standard_modules (load-api))))

(defn warning-for [module-name]
  (when (contains? (unavailable-modules) module-name)
    {:severity :warning
     :message (str "Lua module '" module-name "' is unavailable in CartDark firmware.")}))
