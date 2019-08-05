;; MIT/ISC/WTFPL
;; based on twee-mode.el

(defvar yarn-mode-hook nil)
(add-to-list 'auto-mode-alist '("\\.yarn.txt\\'" . yarn-mode))

(defconst yarn-font-lock-keywords
  (list
   '("\\(\\[\\[\\)\\(.+|\\)?\\([a-zA-Z0-9]+\\)\\(\\]\\]\\)"
     (1 font-lock-keyword-face)
     (3 font-lock-constant-face)
     (4 font-lock-keyword-face))

   '("\\(->\\)" . font-lock-keyword-face)
   '("\\(title:\\)" . font-lock-keyword-face)
   '("\\(---\\)" . font-lock-keyword-face)
   '("\\(===\\)" . font-lock-keyword-face)

   '("\\(<<!\\(\\w+\\)>>\\)"
     . font-lock-constant-face)
   '("\\(<<!\\w+\\) \\(.+?\\)\\(>>\\)"
     (1 font-lock-constant-face)
     (3 font-lock-constant-face))

   '("\\(<<\\(\\w+\\)>>\\)"
     . font-lock-comment-face)
   '("\\(<<\\w+\\) \\(.+?\\)\\(>>\\)"
     (1 font-lock-comment-face)
     (3 font-lock-comment-face))))


(defun yarn-mode ()
  (interactive)
  (kill-all-local-variables)
  (visual-line-mode)
  (set (make-local-variable 'font-lock-defaults) '(yarn-font-lock-keywords))
  (setq major-mode 'yarn-mode)
  (setq mode-name "yarn")
  (run-hooks 'yarn-mode-hook))

(provide 'yarn-mode)
