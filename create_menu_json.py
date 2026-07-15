import json
import os
import uuid


# ---------------- BUILD SIZE LIST ----------------

def build_size_list(item):
    sizes = item.get("sizes", {})
    if not sizes:
        return [], False

    size_list = []
    for index, (size_name, price) in enumerate(sizes.items()):
        size_list.append({
            "nvarParentItemNum": "",
            "nvarSizeItemNum": "",
            "nvarSizeName": size_name,
            "dcmlCostOfGoods": 0,
            "dcmlSizePrice": price,
            "bitIsActive": True,
            "bitIsDeleted": False,
            "bitIsDefaultSize": True if index == 0 else False,
            "intIndex": index
        })

    return size_list, True


# ---------------- BUILD MODIFIER GROUPS ----------------
def build_modifier_groups(item, category, all_modifier_groups):
    # Item-level modifiers (Section 4/4B) are set on the item itself;
    # category-level / shared modifiers (Section 6/7) are set on the category.
    parent_modifier_group_name = item.get("modifierGroup") or category.get("modifierGroup")

    if not parent_modifier_group_name:
        return []

    parent_group = next(
        (m for m in all_modifier_groups if m["groupName"] == parent_modifier_group_name),
        None
    )

    if not parent_group:
        return []

    result_modifiers = []

    for mod_index, option in enumerate(parent_group.get("options", [])):

        child_group_name = option.get("modifierGroup")
        child_group = next(
            (m for m in all_modifier_groups if m["groupName"] == child_group_name),
            None
        )

        modifier_items = []

        if child_group:
            for child_index, child_option in enumerate(child_group.get("options", [])):
                size_prices = []

                if parent_group.get("lstInvSize"):
                    for size_name, price in option.get("prices", {}).items():
                        size_prices.append({
                            "SizeName": size_name,
                            "intSizePriceType": str(price)
                        })

                modifier_items.append({
                    "Modifier": child_option["name"],
                    "ItemNum": "",
                    "ItemPrice": "0.00",
                    "bitIsDeleted": False,
                    "intDisplayIndex": child_index,
                    "bitIsPreSelected": False,
                    "bitHasOverride": False,
                    "ModifierItemSizePrices": size_prices
                })

        result_modifiers.append({
            "nvarModName": option["name"],
            "nvarModNum": "",
            "MinQty": 0,
            "MaxQty": 1,
            "intDisplayIndex": mod_index,
            "intIsInclude": 0,
            "bitIsHalf": False,
            "bitIsDeleted": False,
            "dcmlMOdiGrpPrice": 0,
            "lstModItemOfModGrp": modifier_items
        })

    return result_modifiers



# ---------------- BUILD COMBO MODIFIER GROUPS ----------------
def build_combo_modifier_groups(item):
    combo_groups = item.get("comboGroups") or []

    result_modifiers = []

    for group_index, group in enumerate(combo_groups):
        modifier_items = [
            {
                "nvarModifierItemName": option.get("name"),
                "dcmlPrice": option.get("price") or 0
            }
            for option in group.get("options", [])
        ]

        result_modifiers.append({
            "nvarModName": group.get("groupName"),
            "nvarModNum": "",
            "MinQty": group.get("minQty", 1),
            "MaxQty": group.get("maxQty", 1),
            "intDisplayIndex": group_index,
            "intIsInclude": 1 if group.get("isInclude") else 0,
            "bitIsHalf": False,
            "bitIsDeleted": False,
            "dcmlMOdiGrpPrice": 0,
            "lstModItemOfModGrp": modifier_items
        })

    return result_modifiers


# ---------------- RESOLVE ITEM TYPE ----------------
def resolve_item_type(item, category):
    raw_type = (item.get("itemType") or "").strip().lower()
    if raw_type == "combo":
        return "5"

    name = item.get("name") or ""
    department_name = category.get("category") or ""
    if "combo" in name.lower() or "combo" in department_name.lower():
        return "5"

    return "product"


# ---------------- TRANSFORM ----------------
def transform_menu(input_data):
    output_items = []

    categories = input_data.get("categories", [])
    modifier_groups = input_data.get("modifierGroups", [])

    for category in categories:
        department_name = category.get("category")

        for item in category.get("items", []):

            size_list, has_sizes = build_size_list(item)

            base_price = item.get("price")
            if base_price is None:
                base_price = 0

            item_type = resolve_item_type(item, category)

            if item_type == "5":
                modifiers = build_combo_modifier_groups(item)
            else:
                modifiers = build_modifier_groups(item, category, modifier_groups)

            transformed_item = {
                "DepartmentName": department_name,
                "nvarItemNum": "",
                "nvarItemName": item.get("name"),
                "Id": "",
                "ItemDescription": (item.get("description") or "").lower(),
                "Price": f"{base_price:.2f}",
                "ItemType": item_type,
                "IsModifier": False,
                "ModifierType": None,
                "BonusPoints": 0,
                "dcmlStock": "10.00",
                "bitIsDeleted": False,
                "IsDispalyInMenu": True,
                "nvarDispalyItemName": "",
                "dcmlOnlineItemPrice": f"{base_price:.2f}",
                "DisplayIndex": True,
                "BrandID": "",
                "ServiceMin": 0,
                "IsAllowedZeroPrice": False,
                "IsTracking": False,
                "dcmlLowStockQty": "0.00",
                "bitISSize": has_sizes,
                "lstInvSize": size_list,
                "lstInventoryModifiers": modifiers
            }

            output_items.append(transformed_item)

    return output_items



def save_transformed_json(input_json, unique_id):

    transformed = transform_menu(input_json)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename = f"{unique_id}.json"
    output_path = os.path.join(OUTPUT_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transformed, f, indent=2)

    return output_path