;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.simulator
  (:require [cartdark.process :as process]
            [cartdark.project :as project]
            [clojure.string :as string])
  (:import [java.nio.file Files LinkOption Path]))

(defn- executable? [^Path path]
  (and (Files/isRegularFile path (make-array LinkOption 0))
       (Files/isExecutable path)))

(defn resolve-simulator [{:keys [configured-path environment install-root]
                          :or {environment (System/getenv)
                               install-root (project/->path (System/getProperty "user.dir"))}}]
  (let [path-candidate
        (some (fn [directory]
                (let [candidate (.resolve (project/->path directory) "cartdesk-simulator")]
                  (when (executable? candidate) candidate)))
              (remove string/blank?
                      (string/split (or (get environment "PATH") "")
                                    (re-pattern (java.io.File/pathSeparator)))))
        candidates [(some-> configured-path project/->path)
                    (some-> (get environment "CARTDESK_SIMULATOR") project/->path)
                    path-candidate
                    (.resolve ^Path install-root "tools/cartdesk-simulator/cartdesk-simulator")
                    (.resolve (.getParent ^Path install-root) "cartdesk-simulator/cartdesk-simulator")]]
    (some #(when (and % (executable? %)) (.toAbsolutePath ^Path %)) candidates)))

(defn start! [simulator cart-bin on-line on-exit]
  (process/start! {:command [(str simulator) (str cart-bin)]
                   :directory (.getParent (project/->path simulator))
                   :on-line on-line
                   :on-exit on-exit}))
