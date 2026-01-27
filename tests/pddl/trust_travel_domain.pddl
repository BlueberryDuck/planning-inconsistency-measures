(define (domain trust-travel)
  (:requirements :strips)

  (:predicates
    (at-local)
    (at-remote)
    (trust)
    (partnership)
    (opportunity)
  )

  ;; secure: {at_local, trust} -> {partnership}
  (:action secure
    :parameters ()
    :precondition (and (at-local) (trust))
    :effect (partnership)
  )

  ;; travel: {at_local} -> {at_remote}, delete {at_local, trust, partnership}
  (:action travel
    :parameters ()
    :precondition (at-local)
    :effect (and
      (at-remote)
      (not (at-local))
      (not (trust))
      (not (partnership))
    )
  )

  ;; exploit: {at_remote} -> {opportunity}
  (:action exploit
    :parameters ()
    :precondition (at-remote)
    :effect (opportunity)
  )

  ;; return: {at_remote} -> {at_local}, delete {at_remote}
  (:action return
    :parameters ()
    :precondition (at-remote)
    :effect (and
      (at-local)
      (not (at-remote))
    )
  )
)
