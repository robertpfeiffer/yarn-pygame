;; copyright (c) 2019 Robert Pfeiffer
;; licensed under MIT license
;; based on twee-mode.el (also MIT licensed)
;; from http://tilde.town/~cristo/twee-mode-for-emacs.html

(defvar yarn-mode-hook nil)
(add-to-list 'auto-mode-alist '("\\.yarn.txt\\'" . yarn-mode))

(defconst yarn-font-lock-keywords
  (list
   '("\\(\\[\\[\\)\\(.+|\\)?\\([[:alnum:]\\_-]+\\)\\(\\]\\]\\)"
     (1 font-lock-keyword-face)
     (2 font-lock-string-face)
     (3 font-lock-function-name-face)
     (4 font-lock-keyword-face))

   '("^\\s-*\\(->\\)\\(.+\\)$"
     (1 font-lock-keyword-face)
     (2 font-lock-string-face))
   
   '("^\\(title:\\)\\s-*\\([[:alnum:]\\_-]+\\)\\s-*$"
     (1 font-lock-keyword-face)
     (2 font-lock-function-name-face))
   '("^\\(\\w+:\\).+$" (1 font-lock-keyword-face))

   '("^\\(--*-\\)$" . font-lock-keyword-face)
   '("^\\(==*=\\)$" . font-lock-keyword-face)

   '("\\(<<!\\(\\w+\\)>>\\)"
     . font-lock-constant-face)
   '("\\(<<!\\w+\\) \\(.+?\\)\\(>>\\)"
     (1 font-lock-constant-face)
     (3 font-lock-constant-face))

   '("\\(<<\\)\\(\\w+\\)\\(>>\\)"
     (1 font-lock-comment-face)
     (2 font-lock-keyword-face)
     (3 font-lock-comment-face))
   '("\\(<<\\)\\(\\w+\\) \\(.+?\\)\\(>>\\)"
     (1 font-lock-comment-face)
     (2 font-lock-keyword-face)
     (4 font-lock-comment-face))))

(defun yarn-mode ()
  (interactive)
  (kill-all-local-variables)
  (visual-line-mode)
  (set (make-local-variable 'font-lock-defaults) '(yarn-font-lock-keywords))
  (setq major-mode 'yarn-mode)
  (setq mode-name "yarn")
  (run-hooks 'yarn-mode-hook))

(provide 'yarn-mode)
