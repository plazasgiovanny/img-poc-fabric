import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "img_lib" / "src"))

from img_lib import mapping, normalize
from img_lib.validate import validate_record

TODAY = date(2026, 10, 1)


def test_rsh_mapping_covers_master_columns():
    assert set(mapping.MASTER_COLUMNS) == set(mapping.RSH_TO_INTERNAL)
    assert len(set(mapping.RSH_TO_INTERNAL.values())) == len(mapping.RSH_TO_INTERNAL)
    assert mapping.INTERNAL_TO_RSH["doc_number"] == "RSH_num_documento"


def test_to_internal_population_and_deceased():
    raw = {c: "" for c in mapping.MASTER_COLUMNS}
    raw.update({"RSH_id_llave_maestra": "70001", "RSH_tip_documento": "1", "RSH_seg_nombre": "  ", "_cycle_id": "c"})
    out = mapping.to_internal(raw, "population")
    assert out["origin_id"] == "70001" and out["doc_type"] == "1" and out["second_name"] is None
    assert out["_cycle_id"] == "c"
    inh = mapping.to_internal({"RSH_tip_documento": "1", "RSH_num_documento": "123", "fecha_defuncion": "2026-01-01"},
                              "validation")
    assert inh == {"doc_type": "1", "doc_number": "123", "death_date": "2026-01-01", "origin_id": "INH-1-123"}


def test_document_type_equivalence_master_to_dispersal():
    # tabla explícita del diccionario de dispersión: 1 RC, 2 TI, 3 CC, 4 CE
    expected = {1: 3, 2: 2, 3: 4, 4: 1, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9}
    assert mapping.MASTER_TO_DISPERSAL_DOC_TYPE == expected
    assert mapping.doc_type_to_dispersal("1") == 3  # CC
    assert mapping.doc_type_to_dispersal(4) == 1  # RC
    assert mapping.doc_type_to_dispersal("0") == 0 and mapping.doc_type_to_dispersal(None) == 0
    assert mapping.doc_type_dispersal_text(1) == "Cedula de Ciudadania"
    assert mapping.doc_type_dispersal_text(4) == "Registro Civil"
    assert mapping.doc_type_dispersal_text(0) == "SIN INFORMACION"
    # el texto de cada código coincide entre catálogos (misma persona, mismo documento)
    for m, d in expected.items():
        assert mapping.DOC_TYPE_MASTER[m].lower().split()[0] == mapping.DOC_TYPE_DISPERSAL[d].lower().split()[0]
    assert {mapping.DISPERSAL_TO_MASTER_DOC_TYPE[d] for d in expected.values()} == set(expected)


def test_operator_and_locality_catalogs():
    assert mapping.operator_to_dispersal("DAVIPLATA") == ("DAVIVIENDA", 1)
    assert mapping.operator_to_dispersal("efecty") == ("EFECTY", 5)
    assert mapping.operator_to_dispersal("SIN OPERADOR") == (None, None)
    assert mapping.locality_name(999) == "ZZ-SIN INFORMACION"
    assert mapping.listing_locality_name("ZZ-SIN INFORMACION") == "ZZ- SIN INFORMACION"
    assert mapping.listing_locality_name(None) == "ZZ- SIN INFORMACION"
    assert mapping.listing_locality_name("bosa") == "BOSA"


def test_normalize_new_fields():
    assert normalize.normalize_doc_type("1") == ("1", None)
    assert normalize.normalize_doc_type("CC") == ("1", None)
    assert normalize.normalize_doc_type("0")[1] == "invalid_document_type"
    assert normalize.normalize_sex("2") == ("2", None) and normalize.normalize_sex("3")[1] == "invalid_sex"
    assert normalize.normalize_locality("07") == ("7", None)
    assert normalize.normalize_locality("999") == ("999", None)
    assert normalize.normalize_locality("77")[1] == "invalid_locality"
    assert normalize.normalize_age("34") == (34, None) and normalize.normalize_age("200")[1] == "age_out_of_range"
    assert normalize.normalize_age("")[1] == "age_invalid"
    assert normalize.normalize_renec("") == (None, None) and normalize.normalize_renec("21.0") == ("21", None)
    assert normalize.normalize_renec("x")[1] == "invalid_renec_code"
    assert normalize.normalize_banked("1") == (1, None) and normalize.normalize_banked(None) == (0, None)
    assert normalize.normalize_date("2099-01-01", TODAY)[1] == "date_out_of_range"


def test_validate_record_builds_full_names_and_flags_causes():
    rec = {"doc_type": "1", "doc_number": "99123456", "first_name": "José", "second_name": None, "last_name": "Peña",
           "second_last_name": "Díaz", "birth_date": "1990-05-01", "sex": "2", "age": "36", "locality": "999",
           "banked": "1", "renec_validity": "0"}
    out, causes = validate_record(rec, TODAY)
    assert causes == [] and out["first_names"] == "JOSE" and out["last_names"] == "PEÑA DIAZ"
    assert out["age"] == 36 and out["locality"] == "999"
    _, causes = validate_record({**rec, "birth_date": "2099-01-01", "sex": "9"}, TODAY)
    assert set(causes) == {"date_out_of_range", "invalid_sex"}
    # inhumados: solo tipo, número y fecha de defunción
    out, causes = validate_record({"doc_type": "1", "doc_number": "99123456", "death_date": "2026-01-05"}, TODAY)
    assert causes == [] and "first_names" not in out


def test_age_from_birth():
    assert mapping.age_from_birth("2000-10-02", date(2026, 10, 1)) == 25
    assert mapping.age_from_birth("2000-10-01", date(2026, 10, 1)) == 26
