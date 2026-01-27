(define (problem trust-travel-p1)
  (:domain trust-travel)

  (:init
    (at-local)
    (trust)
  )

  (:goal
    (and
      (partnership)
      (opportunity)
    )
  )
)