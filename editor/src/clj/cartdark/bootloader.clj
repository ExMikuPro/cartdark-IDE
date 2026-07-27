;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.bootloader
  "Small, independent namespace loader for CartDark Studio."
  (:require [clojure.stacktrace :as stacktrace]))

(defonce ^:private load-state (atom nil))

(defn load-boot []
  (let [loaded (promise)
        loader (future
                 (try
                   (require 'cartdark.boot)
                   (deliver loaded true)
                   (catch Throwable throwable
                     (deliver loaded throwable)
                     (throw throwable))))]
    (reset! load-state {:loader loader :loaded loaded})
    nil))

(defn wait-until-boot-loaded []
  (let [result @(-> @load-state :loaded)]
    (when (instance? Throwable result)
      (throw result))))

(defn main [args]
  (let [{:keys [loader]} @load-state]
    @loader
    (try
      ((requiring-resolve 'cartdark.boot/main) args)
      (catch Throwable throwable
        (stacktrace/print-stack-trace throwable)
        (throw throwable)))))
