;; Copyright 2026 ExMikuPro
;; Licensed under the Defold License version 1.0.

(ns cartdark.lua
  "Lua syntax grammar used by CartDark filesystem documents.")

(def open-keywords #{"do" "then" "function" "else" "repeat"})
(def close-keywords #{"end" "until"})

(defn opens-block? [^String line]
  (let [code (-> line
                 (clojure.string/replace #"(['\"]).*?\1" "")
                 (clojure.string/replace #"--.*$" ""))
        tokens (set (re-seq #"[A-Za-z_][A-Za-z_0-9]*" code))]
    (or (clojure.string/ends-with? (clojure.string/trim code) "{")
        (and (some open-keywords tokens)
             (not (some close-keywords tokens))))))

(def grammar
  {:name "CartDark Lua"
   :scope-name "source.lua"
   :indent {:begin opens-block?
            :end #"^\s*((\b(elseif|else|end|until)\b)|(\})|(\)))"}
   :line-comment "--"
   :auto-insert {:characters {\" \" \' \' \[ \] \( \) \{ \}}
                 :close-characters #{\" \' \] \) \}}}
   :patterns
   [{:match #"(?x)(?<![A-Za-z0-9_])(?<number>(?:0[xX][0-9A-Fa-f]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?))(?![A-Za-z0-9_])"
     :name "constant.numeric.lua"}
    {:match #"(?x)(?<![A-Za-z0-9_])(?<keyword>and|break|do|else|elseif|end|false|for|function|goto|if|in|local|nil|not|or|repeat|return|then|true|until|while)(?![A-Za-z0-9_])"
     :name "keyword.control.lua"}
    {:begin #"--\[\["
     :end #"\]\]"
     :name "comment.block.lua"}
    {:match #"--.*$"
     :name "comment.line.double-dash.lua"}
    {:begin #"\""
     :end #"\""
     :name "string.quoted.double.lua"}
    {:begin #"'"
     :end #"'"
     :name "string.quoted.single.lua"}]})
