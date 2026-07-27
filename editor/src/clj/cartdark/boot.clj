;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.boot
  "CartDark Studio boot entry. It intentionally has no dependency on editor.boot."
  (:require [cartdark.app :as app]))

(defn main [args]
  (app/open-project! (first args)))
