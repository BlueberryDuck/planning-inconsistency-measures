(define (domain locked-door)
  (:requirements :strips)

  (:predicates
    (has-key)
    (door-unlocked)
    (in-room)
  )

  ;; unlock: {has_key} -> {door_unlocked}
  ;; NOTE: has_key is NEVER produced - this is the unsolvability source
  (:action unlock
    :parameters ()
    :precondition (has-key)
    :effect (door-unlocked)
  )

  ;; enter: {door_unlocked} -> {in_room}
  (:action enter
    :parameters ()
    :precondition (door-unlocked)
    :effect (in-room)
  )
)