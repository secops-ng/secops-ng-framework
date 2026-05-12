# Notes on Choosing a Lawful Basis (GDPR Article 6(1))

This is operator-to-operator guidance, not legal advice. The lawful basis
under Article 6(1) is a foundational choice that shapes every downstream
data-subject right (Art. 15–22). Get it wrong and the rest of the document
becomes harder to defend.

## The six bases in plain language

| Art. 6(1) | When it fits a security workflow |
|-----------|----------------------------------|
| (a) Consent | Rarely fits security work. Consent must be specific, informed, freely given, and withdrawable. If withdrawing it would break a security control, you almost certainly did not have valid consent. |
| (b) Contract | Fits where the data subject is a counterparty to the operator (member, customer, supplier) and the processing is **necessary** to perform a contract with them. "Necessary" is strict — convenient is not enough. |
| (c) Legal obligation | Fits where a law *requires* the processing. NIS2 Art. 23 reporting is a strong example: the operator is obliged to report incidents, and that obligation grounds the processing of incident data. Cite the article. |
| (d) Vital interests | Rare. Limited to protecting someone's life. |
| (e) Public interest / official authority | Fits public-sector operators and those carrying out tasks in the public interest. Cite the legal basis for the task. |
| (f) Legitimate interests | The most common basis for private-sector security operations. **Requires a balancing test.** |

## The legitimate-interests assessment (LIA)

When relying on Art. 6(1)(f), document the three-part test:

1. **Purpose test** — is there a legitimate interest? State it specifically.
   "Protecting the network and information systems of the entity and its
   members from cyber threats" is a Recital 49 legitimate interest and a
   defensible starting point.
2. **Necessity test** — is the processing necessary to achieve that
   interest? Could a less-intrusive measure achieve the same outcome? If
   yes, use the less-intrusive measure.
3. **Balancing test** — do the data subject's rights and freedoms override
   the legitimate interest? Consider: data subject's reasonable
   expectations, sensitivity of the data, impact on the data subject,
   safeguards in place.

Recital 49 of GDPR explicitly recognises that processing **strictly
necessary and proportionate** for ensuring network and information security
constitutes a legitimate interest. This is helpful but not a blanket
licence. The "strictly necessary" qualifier means minimisation,
pseudonymisation, and retention limits all still apply.

## Multiple bases

A single flow should generally have **one** primary lawful basis. If a
secondary basis applies (e.g. (f) for the day-to-day operation, (c) for the
specific moment of regulatory notification), document both and which one
governs which sub-purpose.

## When the lawful basis changes downstream

If an upstream flow processes data under Art. 6(1)(f) and a downstream
recipient processes the same data under Art. 6(1)(c), that is a **separate
processing operation** with its own basis. Document it as a separate flow.

## References

- Regulation (EU) 2016/679, Article 6(1), Article 9(2), Recital 47, Recital 49.
- EDPB Guidelines 8/2020 on the targeting of social media users
  (not directly applicable but useful for balancing-test reasoning).
- The relevant national supervisory authority's published guidance in the
  operator's jurisdiction of establishment.
