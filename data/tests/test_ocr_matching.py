"""OCR-garbled ingredient names still have to resolve to the right allergen.

A photographed label is the app's second input path, and OCR routinely reads
the capital I in "Iodised" as a lowercase l. When it does that to a *hidden*
allergen name the miss is silent and the verdict comes back clean, which is
the one failure mode this app exists to prevent.

The fuzzy pass cannot cover it: "casein"/"caseln" scores 0.833 while
"calcium carbonate"/"calcium caseinate" — chalk read as milk — scores 0.824,
so any threshold that catches the first reintroduces the second. Hence the
exact match on an OCR-canonical form, and hence these tests pinning both
halves: the slips that must resolve, and the near-misses that must not.
"""

from data.search.fuzzy_match import match_ingredient


def _allergen_ids(token: str) -> set[str]:
    return {m.allergen_id for m in match_ingredient(token)}


class TestOcrSlipsResolve:
    def test_casein_misread_as_caseln_still_flags_milk(self):
        assert "milk" in _allergen_ids("Caseln")

    def test_casein_misread_with_a_digit_still_flags_milk(self):
        assert "milk" in _allergen_ids("Case1n")

    def test_milk_misread_with_capital_i_still_flags_milk(self):
        assert "milk" in _allergen_ids("MiIk")

    def test_gluten_misread_with_a_digit_still_flags_wheat(self):
        assert _allergen_ids("G1uten")


class TestNearMissesStillRejected:
    """The reason the threshold can't simply be lowered."""

    def test_calcium_carbonate_is_not_milk(self):
        # Chalk. Scored 0.824 against "calcium caseinate" and made an oat
        # drink UNSAFE for a dairy allergy.
        assert "milk" not in _allergen_ids("Calcium Carbonate")

    def test_batter_is_not_butter(self):
        # u/a is not an OCR confusion, and batter is its own ingredient.
        assert "milk" not in _allergen_ids("Batter")

    def test_butler_is_not_butter(self):
        # t/l is not in the confusion set — this could be a brand name.
        assert "milk" not in _allergen_ids("Butler")

    def test_cocoa_butter_is_not_milk(self):
        assert "milk" not in _allergen_ids("Cocoa Butter")


class TestOrdinaryMatchingUnaffected:
    def test_exact_names_still_resolve(self):
        assert "milk" in _allergen_ids("Casein")
        assert "milk" in _allergen_ids("Butter")
        assert "milk" in _allergen_ids("Milk Solids")
