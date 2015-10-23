;; Configuration for writing and arranging text

(prelude-require-package 'ledger-mode)
;; setup files ending in “.ledger” to open in ledger-mode
(add-to-list 'auto-mode-alist '("\\.ledger\\'" . ledger-mode))

(prelude-require-package 'writeroom-mode)

(require 'org)
(setq org-folder "~/notes/")

(require 'find-lisp)
;; Add projects folder to agenda files
(setq org-agenda-files (let ((default-directory (concat org-folder "projects")))
                         (file-expand-wildcards "?*.org" t)))


;; Add some individual files to agenda files
(add-to-list 'org-agenda-files (expand-file-name
                                (concat org-folder "gtd.org")))
;; (add-to-list 'org-agenda-files (expand-file-name
;;                                 (concat org-folder "cron.org")))
;; (add-to-list 'org-agenda-files (expand-file-name
;;                                 (concat org-folder "interesting.org")))
(add-to-list 'org-agenda-files (expand-file-name
                                "~/Dropbox/trello-tasks.org"))

(global-set-key (kbd "C-c <f1>")
                (lambda ()
                  (interactive)
                  (find-file (concat org-folder "inbox.org"))))
(global-set-key (kbd "C-c <f2>")
                (lambda ()
                  (interactive)
                  (find-file (concat org-folder "gtd.org"))))
(global-set-key (kbd "C-c <f3>")
                (lambda ()
                  (interactive)
                  (find-file (concat org-folder "/projects"))))
(global-set-key (kbd "C-c <f4>")
                (lambda ()
                  (interactive)
                  (dired "~/dev/")))
(global-set-key (kbd "C-c <f5>")
                (lambda ()
                  (interactive)
                  (find-file dotfiles-folder)))

;; Global org-capture / agenda
(global-set-key (kbd "H-c") 'org-capture)
(global-set-key (kbd "H-a") 'org-agenda)

(defadvice org-capture-finalize
    (after delete-capture-frame activate)
  "Advise capture-finalize to close the frame"
  (if (equal "capture" (frame-parameter nil 'name))
      (delete-frame)))


(setq org-capture-templates
      '(
        ("p" "Post skeleton" entry (file (capture-report-date-file
                                          "~/dev/landing/blog/src/content/posts/"))
         "* Title :tags:
:PROPERTIES:
:date: %t
:slug:
:summary:
Body")
        ("i" "Save to Inbox" entry
         (file+headline (concat org-folder "inbox.org") "inbox") "* %?\n  %i\n")
        ("t" "TODO Item" entry
         (file+headline (concat org-folder "gtd.org") "Tasks") "* TODO %?\n  %i\n")
        ("a" "Appointment or other scheduled item" entry
         (file+headline (concat org-folder "next.org") "Schaduled") "* APPT %?\n  %i\n")
        ("j" "Journal entry" entry (file+datetree (concat org-folder "texts/meta/notetoself.org"))
         "* %?\nEntered on %U\n  %i\n")
        ("r" "Save Recommendation" entry (file+headline (concat org-folder "interesting.org") "Check out") "* %?\n  %i\n")))

(setq org-agenda-skip-scheduled-if-done 'nil)

(setq org-todo-keywords
      '((sequence "TODO(t)" "APPT(a)" "WAIT(w)" "|" "CANCELLED(c)" "DONE(d)")))

(setq org-agenda-custom-commands
      '(
        ("z" "Today"
         ((agenda "" ((org-agenda-ndays 1)))
          (tags-todo "+PRIORITY=\"A\"")
          (todo "TODO")
          ;;(todo "WAIT"))
          ;;(tags-todo "computer|office|phoned")
          ;;(tags "project+CATEGORY=\"elephants\"")
          ;;(tags "review" ((org-agenda-files '("~/org/circuspeanuts.org"))))
          (org-agenda-compact-blocks t)))
        )
      )

(setq system-time-locale "C")

(setq org-agenda-custom-commands
      '(        ;; other commands go here
        ("w" "Week"
         ((agenda "" ((org-agenda-ndays 7))) ;; review upcoming deadlines and appointments
          ;; type "l" in the agenda to review logged items

          (todo "TODO") ;; review all projects (assuming you use todo keywords to designate projects)
          (todo "APPT") ;; review someday/maybe items
          (todo "WAIT")
          (stuck "")))

        ("d" "Day"
         ((agenda "" ((org-agenda-ndays 1))) ;; review upcoming deadlines and appointments
          (tags-todo "+PRIORITY=\"A\"")
          (todo "TODO") ;; review all projects (assuming you use todo keywords to designate projects)
          (todo "MAYBE") ;; review someday/maybe items
          (todo "WAITING"))) ;; review waiting items

        ("c" "Calendar 2 Weeks" agenda ""
         ((org-agenda-ndays 14)                          ;; [1]
          (org-agenda-start-on-weekday 1)               ;; [2]
          (org-agenda-time-grid nil)
          (org-agenda-repeating-timestamp-show-all t)   ;; [3]
          ))
        ))

(setq org-use-fast-todo-selection t)
(setq org-use-fast-tag-selection t)

;;(setq org-catch-invisible-edits 'smart)
(setq org-catch-invisible-edits 'show)
(setq org-ctrl-k-protect-subtree t)

;; Add syntax highlight to src blocks
(setq org-src-fontify-natively t)

;; Refiling TODO
(setq org-refile-targets '((org-agenda-files :maxlevel . 3)))
(setq org-refile-use-outline-path t)
(setq org-outline-path-complete-in-steps t)

(defun own-org-mode-hook ()
  "Modify keymaps and settings used by `org-mode'."
  (visual-line-mode 1)
  (org-indent-mode 1)
  ;;(indent-guide-mode -1)
  ;;(whitespace-mode -1)

  ;; Workaround some smartparens-mode keybindings
  ;;(smartparens-mode -1)
  ;;(autopair-mode)

  ;;(local-set-key (kbd "<C-M-return>") '(org-insert-heading 0 0 nil))

  ;; Avoid arrow keys at all costs
  (local-set-key (kbd "H-N") 'org-move-subtree-up) ; mac workaround
  (local-set-key (kbd "H-p") 'org-move-subtree-up)
  (local-set-key (kbd "H-n") 'org-move-subtree-down)
  (local-set-key (kbd "s-p") 'org-move-subtree-up)
  (local-set-key (kbd "s-n") 'org-move-subtree-down)

  (local-set-key (kbd "M-n") 'org-shiftright)
  (local-set-key (kbd "M-p") 'org-shiftleft)

  (global-unset-key (kbd "C-M-f"))
  (global-unset-key (kbd "C-M-b"))

  (local-set-key (kbd "C-M-f") 'org-shiftmetaright)
  (local-set-key (kbd "C-M-b") 'org-shiftmetaleft)

  (local-set-key (kbd "H-f") 'org-metaright)
  (local-set-key (kbd "H-b") 'org-metaleft)
  )

(add-hook 'org-mode-hook 'own-org-mode-hook)

;; Create filename with datestamp
(defun capture-report-date-file (path)
  (let ((name (read-string "Filename: ")))
    (expand-file-name (format "%s_%s.org"
                              (format-time-string "%Y-%m")
                              name) path)))

;;http://orgmode.org/manual/Template-elements.html
;; Use link to do a quick grep for keyword
;; Eg TODO's in codebase
(org-add-link-type
"grep" 'endless/follow-grep-link)

(defun endless/follow-grep-link (regexp)
  "Run `rgrep' with REGEXP as argument."
  (grep-compute-defaults)
  (rgrep regexp "*" (expand-file-name "./")))