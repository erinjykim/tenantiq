import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

model = SentenceTransformer("all-MiniLM-L6-v2")
# chroma saves everything to "chroma_db" folder in current directory
chroma_client = chromadb.PersistentClient(path="./chroma_db")

import requests
from bs4 import BeautifulSoup
import pypdf
import io
import re

def load_from_url(url, source_name):
    response = requests.get(url)
    content_type = response.headers.get("Content-Type", "")
    
    if "pdf" in content_type or url.endswith(".pdf"):
        # handle PDF URLs
        reader = pypdf.PdfReader(io.BytesIO(response.content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    else:
        # handle web pages
        soup = BeautifulSoup(response.content, "html.parser")
        # remove nav, footer, script, style tags — they add noise
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
    
    # clean up excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return {
        "text": text,
        "source": source_name,
        "url": url
    }

def load_documents(sources):
    documents = []
    for source in sources:
        print(f"Fetching: {source['source_name']}...")
        doc = load_from_url(source["url"], source["source_name"])
        # carry jurisdiction and category forward
        doc["jurisdiction"] = source.get("jurisdiction", "pennsylvania")
        doc["category"] = source.get("category", "general")
        print(f"  Retrieved {len(doc['text'])} characters")
        documents.append(doc)
    return documents

def chunk_documents(documents):
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    all_chunks = []
    for doc in documents:
        chunks = recursive_splitter.split_text(doc["text"])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": doc["source"],
                "chunk_id": i,
                "jurisdiction": doc.get("jurisdiction", "pennsylvania"),
                "category": doc.get("category", "general")
            })
    return all_chunks

def build_knowledge_base(chunks):
    # create Chroma collection
    # get_or_create: if collection already exists, use it; if not, make it
    collection = chroma_client.get_or_create_collection(name="tenant-rights")

    # embed all chunk texts at once
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts).tolist()  # convert to list for Chroma

    # chroma expects a list of ids: unique string id for each chunk
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    # metadata must be a list of dicts, one per chunk
    metadatas = [{
        "source": chunk["source"],
        "chunk_id": chunk["chunk_id"],
        "jurisdiction": chunk.get("jurisdiction", "pennsylvania"),
        "category": chunk.get("category", "general")
    } for chunk in chunks]

    # add to collection
    collection.add(
        documents=texts,            # raw text of each chunk
        embeddings=embeddings,      # embedding vector for each chunk
        metadatas=metadatas,        # source info for each chunk
        ids=ids                     # unique id for each chunk
    )

    print(f"Stored {len(chunks)} chunks in Chroma")
    return collection

sources = [
    {
        "url": "https://www.legis.state.pa.us/cfdocs/legis/LI/uconsCheck.cfm?txtType=HTM&yr=1951&sessInd=0&smthLng=EN&act=0020",
        "source_name": "PA Landlord Tenant Act 1951"
    },
    {
        "url": "https://www.attorneygeneral.gov/wp-content/uploads/2022/06/OAG-Consumer-Guide-Tenant-Landlord-Rights-v.13-web-version.pdf",
        "source_name": "PA Attorney General Tenant Rights Guide"
    },
    {
        "url": "https://www.nplspa.org/file_download/inline/c388937c-2450-4af9-855d-1aa3c20d2d86",
        "source_name": "Neighborhood Legal Services PA Tenant Handbook"
    },
    {
        "url": "https://www.phfa.org/forms/housing_consumer_education/tenant_rights.pdf",
        "source_name": "PA Housing Finance Agency Tenant Rights Guide"
    },
    {
        "url": "https://www.alleghenycounty.us/county-services/property-and-real-estate/real-estate-portals/landlord-tenant-office",
        "source_name": "Allegheny County Landlord Tenant Office"
    },
    {
        "url": "https://pittsburghpa.gov/pgh/tenant-rights",
        "source_name": "City of Pittsburgh Tenant Rights"
    }
]


import json

# if __name__ == "__main__":
#     with open("sources.json", "r") as f:
#         sources = json.load(f)
    
#     documents = load_documents(sources)
#     chunks = chunk_documents(documents)
#     collection = build_knowledge_base(chunks)
#     print(f"Built knowledge base with {len(chunks)} chunks")


# BECAUSE NOT IN USA, CANNOT ACCESS LEGAL WEBSITES SO NEED TO HARDCODE
if __name__ == "__main__":
    chunks = [
        {"text": "A landlord must return the security deposit within 30 days of lease termination. If the landlord fails to provide a written list of damages within 30 days, they forfeit all rights to withhold any portion of the deposit.", "source": "PA Landlord Tenant Act Section 512", "chunk_id": 0, "jurisdiction": "pennsylvania", "category": "statute"},
        {"text": "If a landlord fails to return the security deposit within 30 days, they are liable to the tenant for double the amount wrongfully withheld. The burden of proving actual damages is on the landlord.", "source": "PA Landlord Tenant Act Section 512", "chunk_id": 1, "jurisdiction": "pennsylvania", "category": "statute"},
        {"text": "Security deposits during the first year of any lease cannot exceed two months rent. During the second and subsequent years, the deposit cannot exceed one months rent.", "source": "PA Landlord Tenant Act Section 511.1", "chunk_id": 2, "jurisdiction": "pennsylvania", "category": "statute"},
        {"text": "Before evicting a tenant, a landlord must provide written notice to vacate. For leases of one year or less, the notice must give at least 15 days. For leases of more than one year, at least 30 days notice is required. For non-payment of rent, the notice must give at least 10 days.", "source": "PA Landlord Tenant Act Section 501", "chunk_id": 3, "jurisdiction": "pennsylvania", "category": "statute"},
        {"text": "As a tenant you are entitled to the peaceful use and quiet enjoyment of the property you are renting. Unless your lease says otherwise or there is a serious emergency, your landlord should not come onto the property without your permission.", "source": "Neighborhood Legal Services PA Tenant Handbook", "chunk_id": 4, "jurisdiction": "pittsburgh", "category": "handbook"},
        {"text": "Generally if repairs are needed the landlord should give you at least 24 hours notice before entering. In an emergency such as burst water pipes or smoke detectors activated your landlord has the right to enter to deal with the situation.", "source": "Neighborhood Legal Services PA Tenant Handbook", "chunk_id": 5, "jurisdiction": "pittsburgh", "category": "handbook"},
        {"text": "Landlords are required to maintain rental units in a habitable condition. This includes providing working heat, hot water, electricity, and keeping the structure weatherproof and structurally safe.", "source": "PA Attorney General Tenant Rights Guide", "chunk_id": 6, "jurisdiction": "pennsylvania", "category": "guide"},
        {"text": "A landlord cannot terminate or refuse to renew a lease because a tenant participates in a tenants organization or association. Retaliation for tenant organizing is prohibited under Pennsylvania law.", "source": "PA Landlord Tenant Act Section 205", "chunk_id": 7, "jurisdiction": "pennsylvania", "category": "statute"},
        {"text": "Tenants have the right to invite guests, family, visitors, tradespeople and service providers to their unit. A landlord cannot charge fees or additional rent for a tenant exercising these rights.", "source": "PA Landlord Tenant Act Section 504-A", "chunk_id": 8, "jurisdiction": "pennsylvania", "category": "statute"},
        {"text": "At any time before a writ of possession is executed a tenant facing eviction solely for non-payment of rent can stop the eviction by paying all rent in arrears plus court costs to the constable or sheriff.", "source": "PA Landlord Tenant Act Section 503", "chunk_id": 9, "jurisdiction": "pennsylvania", "category": "statute"},
        {"text": "Security deposits over $100 must be placed in an interest-bearing bank account after the second year of tenancy. The landlord must notify the tenant in writing of the bank name, address, and deposit amount. Interest earned during the first year belongs to the landlord. After the second year the tenant is entitled to the interest.", "source": "PA Landlord Tenant Act Section 511.2", "chunk_id": 10, "jurisdiction": "pennsylvania", "category": "statute"},
        {"text": "When a tenant vacates and leaves personal property behind, the landlord must send written notice before disposing of anything. The tenant has 10 days from the postmark date to retrieve belongings or request storage. If storage is requested the landlord must retain the property for up to 30 days at a location of their choosing. The tenant is responsible for storage costs. A landlord who violates this is liable for triple damages.", "source": "PA Landlord Tenant Act Section 505.1", "chunk_id": 11, "jurisdiction": "pennsylvania", "category": "statute"},
        {"text": "Failure of the tenant to provide the landlord with a new address in writing upon termination of the lease relieves the landlord from any liability under the security deposit return requirements. The 30-day return obligation is only triggered once the landlord has the tenant's forwarding address.", "source": "PA Landlord Tenant Act Section 512", "chunk_id": 12, "jurisdiction": "pennsylvania", "category": "statute"},
    ]
    
    collection = build_knowledge_base(chunks)
    print(f"Built knowledge base with {len(chunks)} chunks")