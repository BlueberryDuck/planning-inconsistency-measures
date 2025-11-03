(define (problem blocksworld-goalmutex)
  (:domain blocksworld-simple)

  (:objects a b)  ; Two blocks

  (:init
    (ontable a)
    (ontable b)
    (clear a)
    (clear b)
    (handempty)
  )

  ;; Goal: IMPOSSIBLE - a must be both clear and have b on top!
  ;; This is TYPE 1 UNSOLVABILITY (Goal Mutex)
  ;; - on(b,a) implies NOT clear(a)
  ;; - But we also require clear(a)
  ;; These goals are MUTUALLY EXCLUSIVE!
  (:goal (and
    (on b a)      ; b is on top of a → a is NOT clear
    (clear a)     ; a is clear → nothing on top of a
  ))
)
