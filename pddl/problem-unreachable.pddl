(define (problem blocksworld-unreachable)
  (:domain blocksworld-simple)

  (:objects a b)  ; Two blocks

  (:init
    (on b a)      ; b is stacked on a
    (ontable a)   ; a is on table
    (clear b)     ; b is clear
    (holding a)   ; INCONSISTENT STATE! We're holding a, but a is on table?
  )
  ;; NOTE: This init state is actually inconsistent in classical planning.
  ;; A better example would require negative preconditions or delete effects.
  ;; This is TYPE 2 UNSOLVABILITY (Unreachable Preconditions) - harder to construct
  ;; in simple STRIPS without negative preconditions.

  ;; For now, this demonstrates an inconsistent initial state
  ;; which is a form of unsolvability at the problem level.
  (:goal (and
    (ontable b)
  ))
)
