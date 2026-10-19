from pathlib import Path


def test_remuneration_history_rows_include_checkbox_for_positive_amounts():
    html = Path(__file__).resolve().parents[1].joinpath('index.html').read_text(encoding='utf-8')

    assert 'const checkboxDinero = reg.dinero > 0 ?' in html
    assert 'registro-remuneracion-check' in html
    assert 'type="checkbox"' in html
    assert 'Egiaztatu' in html
    assert 'Markatu' not in html
    assert 'normalizarMarcadoHistorico' in html
    assert 'reg.marcado = true' in html


def test_checkbox_toggle_persists_to_shared_data():
    html = Path(__file__).resolve().parents[1].joinpath('index.html').read_text(encoding='utf-8')

    assert "checkbox.addEventListener('change'" in html
    assert "sincronizarNube('edit', { registro: registros[index] })" in html
    assert "registros[index].marcado = event.target.checked" in html
