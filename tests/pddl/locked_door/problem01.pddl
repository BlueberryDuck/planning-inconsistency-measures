(define (problem locked-door-p1)
  (:domain locked-door)

  ;; Empty initial state - has_key is not true
  (:init)

  ;; Goal: be in the room
  (:goal
    (in-room)
  )
)