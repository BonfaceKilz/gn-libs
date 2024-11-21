(define-module (gn-libs)
  #:use-module ((gn packages genenetwork) #:select (gn-libs) #:prefix gn:)

  #:use-module (guix gexp)
  #:use-module (guix utils)
  #:use-module (guix packages)
  #:use-module (guix git-download))

(define %source-dir (dirname (dirname (current-source-directory))))

(define vcs-file?
  (or (git-predicate %source-dir)
      (const #t)))

(define-public gn-libs
  (package
    (inherit gn:gn-libs)
    (source
     (local-file "../.."
		 "gn-libs-checkout"
		 #:recursive? #t
		 #:select? vcs-file?))))

(define-public gn-libs-all-tests
  (package
    (inherit gn-libs)
    (arguments
     (substitute-keyword-arguments (package-arguments gn-libs)
       ((#:phases phases #~%standard-phases)
        #~(modify-phases #$phases
            (add-before 'build 'pylint
              (lambda _
                (invoke "pylint" "tests" "gn_libs")))
            (add-after 'pylint 'mypy
              (lambda _
                (invoke "mypy" "--show-erro-codes" ".")))))))
    (native-inputs
     (modify-inputs (package-native-inputs gn-libs)
       (prepend python-mypy)
       (prepend python-pylint)))))

gn-libs
