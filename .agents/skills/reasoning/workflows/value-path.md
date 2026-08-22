# Value Path

Design and test the shortest credible route from first contact to realized value.

## Goal

Make every step between the user and the promised outcome defend itself before
building the full machinery behind it.

## Flow

1. State the value promised to the user.
2. Map the happy path from initial state to realized value, including meaningful
   state transitions, authentication, payment, data mutations, and external
   dependencies.
3. Map important unhappy paths only where they materially affect the core
   experience or decision.
4. Remove, combine, defer, or automate steps aggressively.
5. Prototype the remaining path at the cheapest useful fidelity.
6. Use Wizard-of-Oz, fake data, manual fulfillment, or mocked services where the
   machinery is not itself the uncertainty.
7. Run an Experiment with representative users or workloads.
8. Use Evidence to identify where the path fails, where value is delayed, and
   which real machinery is now justified.

Every step costs user effort and implementation effort. Keep a step only when it
earns both costs.
