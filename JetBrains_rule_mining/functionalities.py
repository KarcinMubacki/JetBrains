import pandas as pd


def parse_and_prune_ruleset(rules_raw, transactions_df, target_item, min_support=0.0, min_confidence=0.0):
    """
    Parses and prunes a rule set with a single target variable.
    Calculates support/confidence from transaction data and removes overly specific rules.

    Parameters:
    - rules_raw: str, multi-line rules
    - transactions_df: pd.DataFrame, binary transaction matrix
    - target_item: str, the RHS target (e.g., 'donor_is_old')
    - min_support: float, optional support filter
    - min_confidence: float, optional confidence filter
    """
    rule_lines = [line.strip() for line in rules_raw.strip().split("\n") if line.strip()]
    parsed_rules = []

    for rule in rule_lines:
        if "=>" not in rule:
            continue
        lhs, rhs = rule.split("=>")
        lhs_items = lhs.strip().split("AND")
        antecedent = frozenset(item.strip() for item in lhs_items)
        parsed_rules.append({
            "Antecedent": antecedent,
            "Consequent": rhs.strip()
        })

    rules_df = pd.DataFrame(parsed_rules)

    def matches_antecedent(row, antecedent):
        for cond in antecedent:
            if cond.startswith("NOT "):
                item = cond[4:]
                if row.get(item, False):
                    return False
            else:
                if not row.get(cond, False):
                    return False
        return True

    supports = []
    confidences = []
    total_rows = len(transactions_df)

    for _, rule in rules_df.iterrows():
        antecedent = rule["Antecedent"]

        matches = transactions_df.apply(lambda row: matches_antecedent(row, antecedent), axis=1)
        matches_with_target = matches & transactions_df[target_item]

        support = matches_with_target.sum() / total_rows
        confidence = (matches_with_target.sum() / matches.sum()) if matches.sum() > 0 else 0.0

        supports.append(support)
        confidences.append(confidence)

    rules_df["Support"] = supports
    rules_df["Confidence"] = confidences

    rules_df = rules_df[(rules_df["Support"] >= min_support) & (rules_df["Confidence"] >= min_confidence)]

    # Step 4: Prune overly specific rules
    def is_overly_specific(idx, rules):
        rule = rules.iloc[idx]
        for j, other in rules.iterrows():
            if j == idx:
                continue
            if other["Consequent"] == rule["Consequent"]:
                if other["Antecedent"].issubset(rule["Antecedent"]):
                    if other["Confidence"] >= rule["Confidence"]:
                        return True
        return False

    rules_df["Overly_Specific"] = rules_df.index.to_series().apply(lambda i: is_overly_specific(i, rules_df))
    pruned_df = rules_df[~rules_df["Overly_Specific"]].drop(columns="Overly_Specific")

    return pruned_df.reset_index(drop=True)