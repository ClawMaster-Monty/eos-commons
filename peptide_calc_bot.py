import discord
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN=os.getenv("PEPTIDE_BOT_TOKEN")
NOTION_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB = os.getenv("NOTION_DATABASE_ID")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

DISCLOSURE = ("\n\n⚠️ **Disclaimer:** This calculator is for educational and informational purposes only. "
    "It does not constitute medical advice. Peptide use carries risks and should only be "
    "undertaken under the guidance of a licensed healthcare provider. "
    "Always consult a qualified professional before starting any protocol. "
    "EOS Commons is not responsible for any adverse outcomes.")

PEPTIDES = {
    "bpc-157": {"name": "BPC-157"}, "tb-500": {"name": "TB-500"},
    "cjc-1295": {"name": "CJC-1295"}, "ipamorelin": {"name": "Ipamorelin"},
    "cjc+ipa": {"name": "CJC-1295 + Ipamorelin"}, "pt-141": {"name": "PT-141"},
    "ghk-cu": {"name": "GHK-Cu"}, "kpv": {"name": "KPV"},
    "retatrutide": {"name": "Retatrutide"}, "semaglutide": {"name": "Semaglutide"},
    "tirzepatide": {"name": "Tirzepatide"},
}

def get_headers():
    return {"Authorization": f"Bearer {NOTION_KEY}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}

def log_to_notion(calc_type, peptide, inputs_str, result_str, units, user):
    if not NOTION_KEY or NOTION_KEY == "YOUR_NOTION_INTEGRATION_TOKEN" or not NOTION_DB: return
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": NOTION_DB},
        "properties": {
            "Name": {"title": [{"text": {"content": f"{peptide} {calc_type} {datetime.now().strftime('%Y-%m-%d')}"}}]},
            "Calculator Type": {"select": {"name": calc_type}},
            "Peptide": {"select": {"name": peptide}},
            "Inputs": {"rich_text": [{"text": {"content": inputs_str}}]},
            "Result": {"rich_text": [{"text": {"content": result_str}}]},
            "Units": {"select": {"name": units}},
            "Discord User": {"rich_text": [{"text": {"content": user}}]},
            "Date": {"date": {"start": datetime.now().isoformat()}},
            "Disclosure Shown": {"checkbox": True}
        }
    }
    try:
        import requests; requests.post(url, headers=get_headers(), json=payload)
    except: pass

@client.event
async def on_ready(): print(f"EOS Calc Bot online as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot or not message.content.startswith("!calc"): return
    args = message.content.split()[1:]
    if not args: await message.channel.send(f"Use `!calc help` for options.{DISCLOSURE}"); return
    cmd, user = args[0].lower(), str(message.author)
    if cmd == "help":
        await message.channel.send("**EOS Peptide Calculator**\n\n`!calc list` - Show all peptides\n`!calc dosage <peptide> <dose_mcg> [weight_kg]` - Dosage calculator\n`!calc recon <peptide> <vial_mg> <water_ml>` - Reconstitution\n`!calc inject <units>` - Units to mL\n`!calc klow [standard|intensive]` - KLOW blend\n`!calc wolverine [standard|intensive]` - Wolverine Stack\n"+DISCLOSURE); return
    if cmd == "list":
        lines = ["**Peptides:**"] + [f"  • {v['name']} ({k})" for k,v in PEPTIDES.items()]
        await message.channel.send("\n".join(lines)+"\n\n**Blends:**\n  • KLOW (klow)\n  • Wolverine (wolverine)"+DISCLOSURE); return
    if cmd == "klow":
        dose = args[1].lower() if len(args)>1 else "standard"
        if dose == "intensive":
            r = "**KLOW — Intensive Dose**\nReconstitution: 5mL BA water\nEach **20 units (0.2mL)** contains:\n  • GHK-Cu: **2 mg**\n  • BPC-157: **400 mcg**\n  • TB-500: **400 mcg**\n  • KPV: **400 mcg**"
            log_to_notion("Blend","KLOW","KLOW intensive","2mg GHK-Cu / 400mcg each","20 units (0.2mL)",user)
        else:
            r = "**KLOW — Standard Dose**\nReconstitution: 5mL BA water\nEach **10 units (0.1mL)** contains:\n  • GHK-Cu: **1 mg**\n  • BPC-157: **200 mcg**\n  • TB-500: **200 mcg**\n  • KPV: **200 mcg**"
            log_to_notion("Blend","KLOW","KLOW standard","1mg GHK-Cu / 200mcg each","10 units (0.1mL)",user)
        await message.channel.send(r+DISCLOSURE); return
    if cmd == "wolverine":
        dose = args[1].lower() if len(args)>1 else "standard"
        if dose == "intensive":
            r = ("**Wolverine — Intensive Dose**\nBPC-157 + TB-500 (1:2 ratio)\nReconstitution: 20mg blend in 2mL BA water\nEach **20 units (0.2mL)** contains:\n  • BPC-157: **~666 mcg**\n  • TB-500: **~1,333 mcg**\n  • Total: **2 mg**\nDose: 5-20 units 2-3x per week")
            log_to_notion("Blend","Wolverine Stack","Wolverine intensive","~666mcg BPC-157 / ~1333mcg TB-500","20 units (0.2mL)",user)
        else:
            r = ("**Wolverine — Standard Dose**\nBPC-157 + TB-500 (1:2 ratio)\nReconstitution: 20mg blend in 2mL BA water\nEach **10 units (0.1mL)** contains:\n  • BPC-157: **~333 mcg**\n  • TB-500: **~667 mcg**\n  • Total: **1 mg**\nDose: 5-20 units 2-3x per week")
            log_to_notion("Blend","Wolverine Stack","Wolverine standard","~333mcg BPC-157 / ~667mcg TB-500","10 units (0.1mL)",user)
        await message.channel.send(r+DISCLOSURE); return
    if cmd == "inject":
        try:
            ml = float(args[1])*0.01
            r = f"**Injection Volume**\n{args[1]} units = **{ml:.2f} mL** (U-100 syringe)"
            log_to_notion("Injection","N/A",f"{args[1]} units",f"{ml:.2f} mL","mL",user)
            await message.channel.send(r+DISCLOSURE)
        except: await message.channel.send(f"Usage: `!calc inject <units>` e.g. `!calc inject 15`{DISCLOSURE}"); return
    if cmd == "recon":
        try:
            pk,vial,water = args[1].lower(),float(args[2]),float(args[3])
            pname = PEPTIDES.get(pk,{}).get("name",pk)
            conc = (vial*1000)/water
            r = (f"**{pname} Reconstitution**\nVial: {vial} mg\nWater: {water} mL BA water\n\nConcentration: **{conc:.0f} mcg/mL** ({conc*0.01:.0f} mcg/unit)\n\nReference:\n  • 200 mcg → {(200/conc)*1000:.1f} units\n  • 300 mcg → {(300/conc)*1000:.1f} units\n  • 500 mcg → {(500/conc)*1000:.1f} units")
            log_to_notion("Reconstitution",pname,f"{vial}mg/{water}mL",f"{conc:.0f} mcg/mL","mcg/mL",user)
            await message.channel.send(r+DISCLOSURE)
        except: await message.channel.send(f"Usage: `!calc recon <peptide> <vial_mg> <water_ml>` e.g. `!calc recon bpc-157 10 5`{DISCLOSURE}"); return
    if cmd == "dosage":
        try:
            pk,dose = args[1].lower(),float(args[2])
            wt = float(args[3]) if len(args)>3 else None
            pname = PEPTIDES.get(pk,{}).get("name",pk)
            conc = 2000
            units = dose/conc
            perkg = f" ({dose/wt:.2f} mcg/kg)" if wt else ""
            r = (f"**{pname} Dosage**\nRequested: **{dose} mcg**{perkg}\nConcentration: 2,000 mcg/mL (20 mcg/unit)\n\nDraw: **{units:.1f} units** ({units*0.01:.2f} mL)")
            log_to_notion("Dosage",pname,f"{dose} mcg / {wt or 'N/A'} kg",f"{units:.1f} units","units",user)
            await message.channel.send(r+DISCLOSURE)
        except: await message.channel.send(f"Usage: `!calc dosage <peptide> <dose_mcg> [weight_kg]` e.g. `!calc dosage bpc-157 300 80`{DISCLOSURE}"); return
    await message.channel.send(f"Unknown command. Use `!calc help` for options.{DISCLOSURE}")

client.run(TOKEN)
