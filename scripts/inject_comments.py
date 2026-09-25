from pathlib import Path

# Add Comments panel to key pages
injects = {
    "frontend/src/app/(app)/contracts/[id]/page.tsx": ("contract", "id"),
    "frontend/src/app/(app)/tasks/[id]/page.tsx": ("task", "id"),
    "frontend/src/app/(app)/counterparties/[id]/page.tsx": ("counterparty", "id"),
}

root = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm")
for rel, (etype, eid) in injects.items():
    p = root / rel
    t = p.read_text(encoding="utf-8")
    if "components/Comments" in t:
        print("skip", rel)
        continue
    if "from \"@/components/ui\"" not in t and "} from \"@/components/ui\";" not in t:
        print("no ui import", rel)
        continue
    # import
    t = t.replace(
        '} from "@/components/ui";',
        '} from "@/components/ui";\nimport Comments from "@/components/Comments";',
        1,
    )
    # inject before final closing of main return - after last Card/modal is hard.
    # Append a comment block at end of page component by replacing the last closing
    # Find a unique marker: "    </div>\n  );\n}" at end of page
    if t.rstrip().endswith("}"):
        # insert Comments before final </div> of the root return if possible
        idx = t.rfind("    </div>\n  );")
        if idx == -1:
            idx = t.rfind("    </div>\r\n  );")
        if idx != -1:
            block = f"\n      <div className=\"mt-4\">\n        <Comments entityType=\"{etype}\" entityId={{{eid}}} />\n      </div>\n"
            t = t[:idx] + block + t[idx:]
            print("injected", rel)
        else:
            print("no marker", rel)
    p.write_text(t, encoding="utf-8")
