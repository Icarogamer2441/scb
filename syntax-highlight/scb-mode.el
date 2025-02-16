;;; scb-mode.el --- Major mode for editing SCB language files -*- lexical-binding: t -*-

;; Author: Your Name
;; Maintainer: Your Name
;; Version: 0.1
;; Keywords: languages, scb
;; URL: http://example.com/scb-mode
;; Package-Requires: ((emacs "24.3"))

;;; Commentary:
;; This file provides `scb-mode', a major mode for editing SCB source files.
;; It offers simple syntax highlighting for:
;;  - Keywords: definitions like datadef, bssdef, funcdef, extern, enumdef, structdef.
;;  - Builtin commands: ret, call, jmp, cmp, jle, add, shl, shr, get.
;;  - Types: int, bytes, bytesbuff, void.
;;  - Variables (prefixed with $) and labels (prefixed with .).

;;; Code:

(defvar scb-font-lock-keywords
  (let ((def-patterns
         '(
           ;; Highlight call statements: capture the function name following 'call'
           ("\\<call\\s-+\\(%[[:alnum:]_]+\\)" 1 'font-lock-function-name-face)
           ;; Highlight function definitions: capture the function name starting with '%'
           ("\\<funcdef\\s-+\\(%[[:alnum:]_]+\\)" 1 'font-lock-function-name-face)
           ;; Highlight extern declarations: capture the function name starting with '%'
           ("\\<extern\\s-+\\(%[[:alnum:]_]+\\)" 1 'font-lock-function-name-face)
           ;; Highlight data definitions: capture the identifier following 'datadef'
           ("\\<datadef\\s-+\\([[:alnum:]_]+\\)" 1 'font-lock-constant-face)
           ;; Highlight struct definitions: capture the identifier following 'structdef'
           ("\\<structdef\\s-+\\([[:alnum:]_]+\\)" 1 'font-lock-type-face)
           ;; Highlight enum definitions: capture the identifier following 'enumdef'
           ("\\<enumdef\\s-+\\([[:alnum:]_]+\\)" 1 'font-lock-type-face)
           ))
        (keywords '("datadef" "bssdef" "funcdef" "extern" "enumdef" "structdef"))
        (builtins '("ret" "call" "jmp" "cmp" "jle" "add" "shl" "shr" "get"))
        (types '("int" "bytes" "bytesbuff" "void")))
    (append def-patterns
            (list
             ;; Fallback highlighting for keywords (if the above capture rules don't apply)
             (cons (regexp-opt keywords 'words) 'font-lock-keyword-face)
             ;; Highlight builtin commands
             (cons (regexp-opt builtins 'words) 'font-lock-builtin-face)
             ;; Highlight data types (built-in)
             (cons (regexp-opt types 'words) 'font-lock-type-face)
             ;; Highlight constructor usage of types (e.g., "Point {")
             '("\\b\\([A-Z][[:alnum:]_]+\\)\\s-*{" 1 'font-lock-type-face)
             ;; Highlight enum access usage (e.g., "Color::")
             '("\\b\\([A-Z][[:alnum:]_]+\\)::" 1 'font-lock-type-face)
             ;; Highlight datadef usage (e.g., "fmt:" in function calls)
             '("[(,]\\s-*\\([[:lower:]][[:alnum:]_]+\\):" 1 'font-lock-constant-face)
             ;; Highlight variables (starting with $)
             '("\\$[[:alnum:]_]+" . font-lock-variable-name-face)
             ;; Highlight labels (starting with .)
             '("\\.[[:alnum:]_]+" . font-lock-constant-face))))
  "Keyword highlighting specification for `scb-mode'.")

;;;###autoload
(define-derived-mode scb-mode prog-mode "SCB"
  "Major mode for editing SCB language source files."
  ;; Set comment syntax (comments start with "#")
  (setq-local comment-start "#")
  (setq-local comment-end "")
  ;; Use the defined font-lock keywords
  (setq-local font-lock-defaults '(scb-font-lock-keywords))
)

;;;###autoload
(add-to-list 'auto-mode-alist '("\\.scb\\'" . scb-mode))

(provide 'scb-mode)
;;; scb-mode.el ends here
