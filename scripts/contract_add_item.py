from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\frontend\src\app\(app)\contracts\[id]\page.tsx")
t = p.read_text(encoding="utf-8")

if "itemOpen" not in t:
    t = t.replace(
        "  const [actOpen, setActOpen] = useState(false);",
        "  const [actOpen, setActOpen] = useState(false);\n  const [itemOpen, setItemOpen] = useState(false);\n  const [services, setServices] = useState<{ id: string; name: string; unit: string; base_price: string }[]>([]);\n  const [itemForm, setItemForm] = useState({ service_id: \"\", name_snapshot: \"\", unit_snapshot: \"шт\", quantity: \"1\", unit_price: \"0\" });",
    )
    t = t.replace(
        "      const data = await apiGet<Contract>(`/contracts/${id}`);",
        "      const data = await apiGet<Contract>(`/contracts/${id}`);\n      const svcs = await apiGet<{ id: string; name: string; unit: string; base_price: string }[]>(`/services`).catch(() => []);\n      setServices(svcs);",
    )
    t = t.replace(
        "          <Button onClick={() => setActOpen(true)}>+ Акт / часть</Button>",
        "          <>\n            <Button variant=\"secondary\" onClick={() => setItemOpen(true)}>+ Услуга</Button>\n            <Button onClick={() => setActOpen(true)}>+ Акт / часть</Button>\n          </>",
    )
    # add functions and modal before return
    t = t.replace(
        "  async function addAct() {",
        """  async function addItem() {
    setSaving(true);
    try {
      await apiPost(`/contracts/${id}/items`, {
        service_id: itemForm.service_id || null,
        name_snapshot: itemForm.name_snapshot,
        unit_snapshot: itemForm.unit_snapshot,
        quantity: itemForm.quantity || "1",
        unit_price: itemForm.unit_price || "0",
      });
      setItemOpen(false);
      setItemForm({ service_id: "", name_snapshot: "", unit_snapshot: "шт", quantity: "1", unit_price: "0" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось добавить услугу");
    } finally {
      setSaving(false);
    }
  }

  async function addAct() {""",
    )
    t = t.replace(
        "      <Modal open={actOpen}",
        """      <Modal open={itemOpen} title="Добавить услугу" onClose={() => setItemOpen(false)}>
        <div className="grid gap-3">
          <Field label="Из справочника услуг">
            <Select
              value={itemForm.service_id}
              onChange={(e) => {
                const s = services.find((x) => x.id === e.target.value);
                setItemForm({
                  ...itemForm,
                  service_id: e.target.value,
                  name_snapshot: s?.name || itemForm.name_snapshot,
                  unit_snapshot: s?.unit || itemForm.unit_snapshot,
                  unit_price: s?.base_price || itemForm.unit_price,
                });
              }}
            >
              <option value="">— вручную —</option>
              {services.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Наименование *">
            <Input
              value={itemForm.name_snapshot}
              onChange={(e) => setItemForm({ ...itemForm, name_snapshot: e.target.value })}
            />
          </Field>
          <div className="grid grid-cols-3 gap-2">
            <Field label="Кол-во">
              <Input value={itemForm.quantity} onChange={(e) => setItemForm({ ...itemForm, quantity: e.target.value })} />
            </Field>
            <Field label="Ед.">
              <Input value={itemForm.unit_snapshot} onChange={(e) => setItemForm({ ...itemForm, unit_snapshot: e.target.value })} />
            </Field>
            <Field label="Цена">
              <Input value={itemForm.unit_price} onChange={(e) => setItemForm({ ...itemForm, unit_price: e.target.value })} />
            </Field>
          </div>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setItemOpen(false)}>
            Отмена
          </Button>
          <Button onClick={addItem} disabled={saving || !itemForm.name_snapshot.trim()}>
            Добавить
          </Button>
        </div>
      </Modal>

      <Modal open={actOpen}""",
    )
p.write_text(t, encoding="utf-8")
print("ok", "itemOpen" in t)
