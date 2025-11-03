(define (domain blocksworld-simple)
  (:requirements :strips)

  (:predicates
    (on ?x ?y)       ; block x is on y
    (ontable ?x)     ; block x is on the table
    (clear ?x)       ; block x has nothing on top
    (holding ?x)     ; robot arm is holding block x
    (handempty)      ; robot arm is empty
  )

  ;; Pick up a block from the table
  (:action pick-up
    :parameters (?x)
    :precondition (and (clear ?x) (ontable ?x) (handempty))
    :effect (and (holding ?x)
                 (not (ontable ?x))
                 (not (clear ?x))
                 (not (handempty)))
  )

  ;; Put down a block on the table
  (:action put-down
    :parameters (?x)
    :precondition (holding ?x)
    :effect (and (ontable ?x)
                 (clear ?x)
                 (handempty)
                 (not (holding ?x)))
  )

  ;; Stack block x on top of block y
  (:action stack
    :parameters (?x ?y)
    :precondition (and (holding ?x) (clear ?y))
    :effect (and (on ?x ?y)
                 (clear ?x)
                 (handempty)
                 (not (holding ?x))
                 (not (clear ?y)))
  )

  ;; Unstack block x from block y
  (:action unstack
    :parameters (?x ?y)
    :precondition (and (on ?x ?y) (clear ?x) (handempty))
    :effect (and (holding ?x)
                 (clear ?y)
                 (not (on ?x ?y))
                 (not (clear ?x))
                 (not (handempty)))
  )
)
