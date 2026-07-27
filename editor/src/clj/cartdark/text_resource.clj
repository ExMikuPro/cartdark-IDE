;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.text-resource
  "Dynamo Graph adapter for ordinary UTF-8 files opened in Defold's code view."
  (:require [dynamo.graph :as g]
            [editor.code.data :as data]
            [editor.code.resource :as code-resource]
            [editor.types :as types]))

(g/defnode TextResource
  (property path g/Any)
  (property original-lines types/Lines)
  (property modified-lines types/Lines)
  (property cursor-ranges code-resource/CursorRanges
            (default [data/document-start-cursor-range]))
  (property invalidated-rows code-resource/InvalidatedRows (default []))
  (property modified-indent-type code-resource/IndentType
            (default code-resource/default-indent-type))
  (property regions code-resource/Regions (default []))

  (output lines types/Lines (g/fnk [modified-lines] modified-lines))
  (output indent-type code-resource/IndentType
          (g/fnk [modified-indent-type] modified-indent-type))
  (output completions g/Any (g/constantly {}))
  (output dirty g/Bool (g/fnk [original-lines modified-lines]
                         (not= original-lines modified-lines)))
  (output resource-properties g/Any (g/constantly {}))
  (output keymap g/Any (g/constantly {}))
  (output open-views g/Any (g/constantly {})))

(defn make! [graph path lines]
  (g/make-node! graph TextResource
                :path path
                :original-lines lines
                :modified-lines lines))

(defn mark-saved! [node-id]
  (g/set-property! node-id :original-lines (g/node-value node-id :modified-lines)))
