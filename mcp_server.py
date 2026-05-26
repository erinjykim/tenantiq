import asyncio
import sys
import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "/Users/erinkim/Desktop/tenant/tenantiq-embeddings")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("tenantiq")

_collection = None

def get_collection():
    global _collection
    if _collection is None:
        chroma_client = chromadb.PersistentClient(
            path="/Users/erinkim/Desktop/tenant/tenantiq-embeddings/chroma_db"
        )
        _collection = chroma_client.get_collection(name="tenant-rights")
    return _collection

STATUTE_INDEX = {
    "section 512": "A landlord must return the security deposit within 30 days of lease termination. If the landlord fails to provide a written list of damages within 30 days, they forfeit all rights to withhold any portion of the deposit. If a landlord fails to return the security deposit within 30 days, they are liable to the tenant for double the amount wrongfully withheld.",
    "section 511.1": "Security deposits during the first year of any lease cannot exceed two months rent. During the second and subsequent years, the deposit cannot exceed one months rent. Any attempted waiver of these limits by a tenant is void and unenforceable.",
    "section 501": "Before evicting a tenant, a landlord must provide written notice to vacate. For leases of one year or less, the notice must give at least 15 days. For leases of more than one year, at least 30 days notice is required. For non-payment of rent, the notice must give at least 10 days.",
    "section 205": "A landlord cannot terminate or refuse to renew a lease because a tenant participates in a tenants organization or association. Retaliation for tenant organizing is prohibited under Pennsylvania law.",
    "section 504-a": "Tenants have the right to invite guests, family, visitors, tradespeople and service providers to their unit. A landlord cannot charge fees or additional rent for a tenant exercising these rights. Any lease provision attempting to restrict this right is void and unenforceable.",
    "section 503": "At any time before a writ of possession is executed, a tenant facing eviction solely for non-payment of rent can stop the eviction by paying all rent in arrears plus court costs to the constable or sheriff.",
    "section 505.1": "When a tenant vacates and leaves personal property behind, the landlord must send written notice before disposing of anything. The tenant has 10 days from the postmark date to retrieve belongings or request storage. If storage is requested the landlord must retain the property for up to 30 days. A landlord who violates this is liable for triple damages.",
    "section 511.2": "Security deposits over $100 must be placed in an interest-bearing bank account after the second year of tenancy. The landlord must notify the tenant in writing of the bank name, address, and deposit amount.",
}

CATEGORY_SEARCH_TERMS = {
    "security_deposit": "security deposit return timeline damages withheld",
    "eviction_and_notice": "eviction notice quit writ possession landlord procedure",
    "habitability_and_repairs": "habitability repairs heat hot water landlord duty maintain",
    "landlord_entry": "landlord entry notice permission 24 hours privacy quiet enjoyment",
    "lease_terms": "lease agreement terms conditions sublease provisions",
    "tenant_retaliation": "retaliation prohibited tenant complaint organizing",
    "rent_payment": "rent payment late fee increase",
    "general_rights": "tenant rights Pennsylvania landlord"
}

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_tenant_law",
            description="Search Pennsylvania tenant rights law. Returns relevant statute passages for a given query. Use this when a user asks about their rights as a tenant in Pennsylvania.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The tenant's question or situation in natural language"
                    },
                    "category": {
                        "type": "string",
                        "description": "Legal category: security_deposit, eviction_and_notice, habitability_and_repairs, landlord_entry, lease_terms, tenant_retaliation, rent_payment, general_rights",
                        "default": "general_rights"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_statute",
            description="Retrieve the full text of a specific Pennsylvania landlord-tenant statute by citation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "citation": {
                        "type": "string",
                        "description": "The statute citation, e.g. 'Section 512' or 'Section 501'"
                    }
                },
                "required": ["citation"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "search_tenant_law":
        from retrieve import retrieve

        query = arguments["query"]
        category = arguments.get("category", "general_rights")
        enriched_query = f"{query} {CATEGORY_SEARCH_TERMS.get(category, '')}"

        try:
            collection = get_collection()
            results = retrieve(enriched_query, collection, top_k=3)

            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            passages = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                similarity = round(1 - dist, 3)
                passages.append(
                    f"[Source: {meta['source']} | Relevance: {similarity}]\n{doc}"
                )

            output = f"Found {len(passages)} relevant passages:\n\n"
            output += "\n\n---\n\n".join(passages)
            output += "\n\n⚠️ This information is for educational purposes only and is not legal advice."

        except Exception as e:
            output = f"Error retrieving passages: {str(e)}"

        return [types.TextContent(type="text", text=output)]

    elif name == "get_statute":
        citation = arguments["citation"].lower()

        statute_text = None
        for key in STATUTE_INDEX:
            if key in citation or citation in key:
                statute_text = STATUTE_INDEX[key]
                break

        if statute_text:
            output = f"Pennsylvania Landlord Tenant Act — {arguments['citation']}\n\n{statute_text}\n\n⚠️ This is not legal advice."
        else:
            available = ", ".join(STATUTE_INDEX.keys())
            output = f"Citation '{arguments['citation']}' not found.\n\nAvailable sections: {available}"

        return [types.TextContent(type="text", text=output)]

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())