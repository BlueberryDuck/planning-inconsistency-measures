(define (problem blocksworld-solvable)
  (:domain blocksworld-simple)

  (:objects a b c)  ; Three blocks

  (:init
    (ontable a)
    (ontable b)
    (ontable c)
    (clear a)
    (clear b)
    (clear c)
    (handempty)
  )

  ;; Goal: Stack b on a, and c on b
  ;;   [c]
  ;;   [b]
  ;;   [a]
  ;; -------
  ;; This is SOLVABLE
  (:goal (and
    (on b a)
    (on c b)
  ))
)
