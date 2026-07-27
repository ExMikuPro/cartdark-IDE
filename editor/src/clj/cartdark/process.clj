;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.process
  "Cancelable asynchronous process runner with independent stdout/stderr streams."
  (:refer-clojure :exclude [run!])
  (:require [clojure.java.io :as io])
  (:import [java.nio.charset StandardCharsets]
           [java.nio.file Path]
           [java.util.concurrent TimeUnit]))

(defn- pump-lines! [stream stream-name on-line]
  (with-open [reader (io/reader stream :encoding "UTF-8")]
    (doseq [line (line-seq reader)]
      (on-line stream-name line))))

(defn start!
  [{:keys [command directory environment on-line on-exit]
    :or {on-line (fn [_ _])
         on-exit (fn [_])}}]
  (let [builder (ProcessBuilder. ^java.util.List (mapv str command))]
    (when directory
      (.directory builder (.toFile ^Path directory)))
    (when environment
      (.putAll (.environment builder) environment))
    (let [process (.start builder)
          stdout (future (pump-lines! (.getInputStream process) :stdout on-line))
          stderr (future (pump-lines! (.getErrorStream process) :stderr on-line))
          completion (future
                       (let [exit-code (.waitFor process)]
                         @stdout
                         @stderr
                         (on-exit exit-code)
                         exit-code))]
      {:process process
       :completion completion
       :cancel! (fn []
                  (.destroy process)
                  (when-not (.waitFor process 2 TimeUnit/SECONDS)
                    (.destroyForcibly process)))})))

(defn run!
  "Synchronous helper for tests and non-UI callers."
  [options]
  (let [{:keys [completion] :as handle} (start! options)]
    (assoc handle :exit-code @completion)))
