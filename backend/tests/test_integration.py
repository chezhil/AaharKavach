"""End-to-end checks over the shared handlers.

These exercise the real wiring — Role 2's ontology, the reasoning layer and
Cedar — with no network: every product here comes from the bundled catalogue.
"""

import pytest

from shared import api, catalogue
from shared.adapters import ingredient_from_token
from shared.cedar_utils import check_permission
from shared.contracts import Product, Profile, Restriction
from shared.reasoning import allergen_ids_for, evaluate_deterministic

ADMIN = api.Caller({"X-Aahar-Role": "Admin", "X-Aahar-User": "user_123"})
MEMBER = api.Caller({"X-Aahar-Role": "Member", "X-Aahar-User": "user_456"})

HOUSEHOLD = [
    Profile(id="a", name="Aaditya", restrictions=[
        Restriction("r1", "Gluten", "MODERATE"), Restriction("r2", "Soy", "MILD")]),
    Profile(id="k", name="Aryan", restrictions=[
        Restriction("r3", "Peanuts", "SEVERE"), Restriction("r4", "Dairy", "MODERATE")]),
    Profile(id="n", name="Naman", restrictions=[
        Restriction("r5", "Latex", "MODERATE"), Restriction("r6", "Vegetarian", "MILD")]),
]


def verdicts(product: Product):
    result = evaluate_deterministic(product, HOUSEHOLD)
    return {e.profile_name: e.verdict for e in result.profile_evaluations}


# ------------------------------------------------------------- matching


@pytest.mark.parametrize(
    "label,expected",
    [
        ("Gluten", "wheat_gluten"),
        ("Dairy", "milk"),
        ("Peanuts", "peanuts"),
        ("Tree Nuts", "tree_nuts"),
        ("Soy", "soybeans"),
        ("Sesame", "sesame"),
        ("Latex", "latex"),
    ],
)
def test_restriction_labels_map_to_allergen_ids(label, expected):
    assert expected in allergen_ids_for(label)


def test_qualified_indian_label_terms_are_caught():
    """Regression: these all silently passed as clean before containment matching."""
    product = Product(barcode="t1", name="Test", ingredients=[
        ingredient_from_token(t) for t in
        ["Refined Wheat Flour (Maida)", "Groundnut Oil", "Toned Milk", "Kaju"]
    ])
    result = evaluate_deterministic(product, HOUSEHOLD)
    flagged = {
        f.matched_allergen
        for e in result.profile_evaluations
        for f in e.flagged_ingredients
    }
    assert any("Gluten" in a for a in flagged)
    assert any("Milk" in a for a in flagged)


def test_cocoa_butter_is_not_dairy():
    """`butter` is a milk synonym; cocoa butter contains none."""
    product = catalogue.lookup("8908003847412")  # 70% dark chocolate
    assert verdicts(product) == {"Aaditya": "SAFE", "Aryan": "SAFE", "Naman": "SAFE"}


def test_severe_allergen_outranks_a_mild_one():
    result = evaluate_deterministic(catalogue.lookup("5000159461122"), HOUSEHOLD)
    aryan = next(e for e in result.profile_evaluations if e.profile_name == "Aryan")
    assert aryan.verdict == "UNSAFE"
    assert aryan.flagged_ingredients[0].profile_severity == "SEVERE"


def test_cross_reactivity_is_marked_and_softened():
    result = evaluate_deterministic(catalogue.lookup("8901030865278"), HOUSEHOLD)  # banana chips
    naman = next(e for e in result.profile_evaluations if e.profile_name == "Naman")
    assert naman.verdict == "CAUTION"
    flag = naman.flagged_ingredients[0]
    assert flag.cross_reactive is True
    assert flag.profile_severity == "MILD"  # downgraded from the profile's MODERATE


def test_one_evaluation_per_selected_profile():
    result = evaluate_deterministic(catalogue.lookup("5000159461122"), HOUSEHOLD)
    assert len(result.profile_evaluations) == len(HOUSEHOLD)


def test_thin_record_reports_low_confidence():
    result = evaluate_deterministic(catalogue.lookup("8904004401234"), HOUSEHOLD)
    assert result.confidence == "LOW"
    assert result.data_quality_note


# ----------------------------------------------------------------- api


def test_profiles_seed_and_list():
    status, payload = api.list_profiles(ADMIN)
    assert status == 200
    assert {p["name"] for p in payload} == {"Aaditya", "Aryan", "Naman"}


def test_profile_crud_round_trip():
    status, created = api.create_profile(ADMIN, {
        "name": "Jyothi", "household_role": "MEMBER",
        "restrictions": [{"label": "Tree Nuts", "severity": "SEVERE"}],
    })
    assert status == 201

    status, updated = api.update_profile(ADMIN, created["id"], {
        "name": "Jyothi R", "household_role": "MEMBER",
        "restrictions": [{"label": "Tree Nuts", "severity": "MILD"}],
    })
    assert status == 200 and updated["restrictions"][0]["severity"] == "MILD"

    status, _ = api.remove_profile(ADMIN, created["id"])
    assert status == 204
    _, remaining = api.list_profiles(ADMIN)
    assert created["id"] not in {p["id"] for p in remaining}


def test_evaluate_records_history():
    api.evaluate_endpoint(ADMIN, {"barcode": "8901063152762",
                                  "profile_ids": ["adult_1", "kid_1", "adult_2"]})
    status, history = api.history_endpoint(ADMIN)
    assert status == 200
    assert history and history[0]["product"]["barcode"] == "8901063152762"


def test_evaluate_needs_somebody_to_check_against():
    with pytest.raises(api.ApiError) as exc:
        api.evaluate_endpoint(ADMIN, {"barcode": "8901063152762", "profile_ids": ["nobody"]})
    assert exc.value.status == 400


def test_unknown_barcode_is_404_not_an_empty_product():
    with pytest.raises(api.ApiError) as exc:
        api.lookup_product("0000000000000")
    assert exc.value.status == 404


def test_compare_picks_the_safer_product():
    status, payload = api.compare_endpoint(ADMIN, {
        "barcode_a": "5000159461122",      # Snickers — severe for Aryan
        "barcode_b": "8908003847412",      # nut-free dark chocolate
        "profile_ids": ["adult_1", "kid_1", "adult_2"],
    })
    assert status == 200
    assert payload["safer_pick"] == "B"
    assert payload["reason"]


# --------------------------------------------------------------- cedar


@pytest.mark.parametrize(
    "role,user,action,owner,allowed",
    [
        ("Admin", "u1", "ReadProfile", "u2", True),
        ("Admin", "u1", "CreateProfile", "u1", True),
        ("Admin", "u1", "UpdateProfile", "u2", True),
        ("Admin", "u1", "DeleteProfile", "u2", True),
        ("Member", "u2", "ReadProfile", "u1", True),
        ("Member", "u2", "UpdateProfile", "u1", False),
        ("Member", "u2", "UpdateProfile", "u2", True),
        ("Member", "u2", "CreateProfile", "u2", False),
        ("Child", "u3", "UpdateProfile", "u3", False),
    ],
)
def test_cedar_household_rules(role, user, action, owner, allowed):
    assert check_permission(user, role, "hh_1", action, "p1", owner, "hh_1") is allowed


def test_cedar_blocks_other_households():
    assert check_permission("u9", "Admin", "hh_2", "ReadProfile", "p1", "u1", "hh_1") is False


def test_member_cannot_delete_a_profile_through_the_api():
    with pytest.raises(api.ApiError) as exc:
        api.remove_profile(MEMBER, "kid_1")
    assert exc.value.status == 403


# --------------------------------------------------- deployment layout


def test_cedar_policy_file_is_found():
    """Fails closed if missing, so every profile request would 403 on AWS."""
    from shared.cedar_utils import POLICY_FILE

    assert POLICY_FILE.is_file(), f"Cedar policies not found at {POLICY_FILE}"


def test_cedar_policy_lookup_handles_the_lambda_layout(tmp_path, monkeypatch):
    """In a Lambda package the policies sit beside the code, not a level up."""
    from shared import cedar_utils

    lambda_root = tmp_path / "task"
    (lambda_root / "shared").mkdir(parents=True)
    (lambda_root / "policies").mkdir()
    (lambda_root / "policies" / "policies.cedar").write_text("// test")

    monkeypatch.setattr(cedar_utils, "__file__", str(lambda_root / "shared" / "cedar_utils.py"))
    found = cedar_utils._find_policy_file()
    assert found == lambda_root / "policies" / "policies.cedar"


def test_policy_path_can_be_overridden(tmp_path, monkeypatch):
    policy = tmp_path / "custom.cedar"
    policy.write_text("// test")
    monkeypatch.setenv("AAHAR_CEDAR_POLICIES", str(policy))
    from shared import cedar_utils

    assert cedar_utils._find_policy_file() == policy


# ------------------------------------------- agent / rulebook boundary


def test_agent_flags_without_index_support_are_marked_and_defanged():
    """The model reaches past the knowledge base; the verdict must not follow.

    Regression for a Monster Energy scan where the agent flagged taurine as
    animal-derived — outdated, absent from the index, and different on every
    run, while the rulebook said SAFE.
    """
    from shared.contracts import EvaluationResult, FlaggedIngredient, ProfileEvaluation
    from shared.reasoning import reconcile

    profile = Profile(
        id="n", name="Naman",
        restrictions=[Restriction("r1", "Vegetarian", "MILD")],
    )
    result = EvaluationResult(
        confidence="MEDIUM",
        profile_evaluations=[
            ProfileEvaluation(
                profile_id="n", profile_name="Naman", verdict="CAUTION",
                summary="Potential animal-derived ingredients.",
                flagged_ingredients=[
                    FlaggedIngredient(
                        ingredient="Taurine",
                        matched_allergen="Animal-derived",
                        profile_severity="MODERATE",
                        explanation="Taurine is often derived from animal sources.",
                    )
                ],
            )
        ],
    )

    reconciled = reconcile(result, [profile])
    evaluation = reconciled.profile_evaluations[0]

    flag = evaluation.flagged_ingredients[0]
    assert flag.unverified is True          # surfaced, not silently dropped
    assert flag.profile_severity == "MILD"  # cannot masquerade as a firm match
    assert evaluation.verdict == "SAFE"     # and cannot drive the verdict


def test_reconcile_keeps_flags_the_index_supports():
    from shared.contracts import EvaluationResult, FlaggedIngredient, ProfileEvaluation
    from shared.reasoning import reconcile

    profile = Profile(
        id="k", name="Aryan",
        restrictions=[Restriction("r1", "Peanuts", "SEVERE")],
    )
    result = EvaluationResult(
        confidence="HIGH",
        profile_evaluations=[
            ProfileEvaluation(
                profile_id="k", profile_name="Aryan", verdict="UNSAFE",
                summary="Contains peanuts.",
                flagged_ingredients=[
                    FlaggedIngredient(
                        ingredient="Peanuts", matched_allergen="Peanuts",
                        profile_severity="SEVERE",
                        explanation="Peanuts are a severe allergen for Aryan.",
                    )
                ],
            )
        ],
    )

    evaluation = reconcile(result, [profile]).profile_evaluations[0]
    assert evaluation.flagged_ingredients[0].unverified is False
    assert evaluation.flagged_ingredients[0].profile_severity == "SEVERE"
    assert evaluation.verdict == "UNSAFE"


def test_measurements_are_not_ingredients():
    """"300ppm" came off a caffeine line and rendered as its own chip."""
    from shared.adapters import is_quantity

    for token in ("300ppm", "30mg/100ml", "(400 mg/100ml)", "12%", "100g", "2"):
        assert is_quantity(token), token
    for token in ("Taurine", "Salt", "E322", "Vitamin B12", "Soy Lecithin"):
        assert not is_quantity(token), token


def test_upstream_outage_is_not_reported_as_not_found(monkeypatch):
    """A rate-limited lookup must not claim the product doesn't exist.

    "Not in the database" sends someone to photograph a label when waiting
    a moment would have worked.
    """
    from data.client.openfoodfacts import OffApiError

    def rate_limited(barcode, *a, **k):
        raise OffApiError("Open Food Facts rate limit hit — try again shortly")

    monkeypatch.setattr("data.services.scan_barcode", rate_limited)

    # A barcode the bundled catalogue cannot cover.
    with pytest.raises(api.ApiError) as exc:
        api.lookup_product("1111111111111")
    assert exc.value.status == 503
    assert "again" in exc.value.message.lower()


def test_outage_still_falls_back_to_the_bundled_catalogue(monkeypatch):
    from data.client.openfoodfacts import OffApiError

    def rate_limited(barcode, *a, **k):
        raise OffApiError("rate limited")

    monkeypatch.setattr("data.services.scan_barcode", rate_limited)
    product = api.lookup_product("5000159461122")   # in the catalogue
    assert product.source == "OFFLINE_CATALOGUE"
    assert product.ingredients


def test_a_product_body_keeps_its_nutrition_panel():
    """A product sent as a request body must not lose its nutrition panel.

    _product_from_payload read Open Food Facts' raw `nutriments` key, but the
    wire format this API both emits and documents is `nutritional_stats` — the
    two never met, so any product round-tripped through /api/evaluate as a body
    came back with its panel silently emptied, and the result screen (which
    renders from the stored scan) had nothing left to chart.
    """
    stats = {"Energy_kcal": 481.0, "Protein": 8.6, "Sugars": 51.8}

    ours = api._product_from_payload(
        {"barcode": "1", "name": "Round Trip", "nutritional_stats": stats}
    )
    assert ours.nutritional_stats == stats

    # Open Food Facts' own key is still accepted, for anything upstream that
    # hands the raw record straight over.
    theirs = api._product_from_payload(
        {"barcode": "1", "name": "Round Trip", "nutriments": stats}
    )
    assert theirs.nutritional_stats == stats

    # A product with no panel stays empty rather than becoming None.
    assert api._product_from_payload({"barcode": "1", "name": "Bare"}).nutritional_stats == {}
