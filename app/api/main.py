from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.modal import Product

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def welcome():
    return {"status": True, "message": "Product OK"}


@app.get("/products", response_model=list[Product])
def allProducts():
    return [getProduct(pk) for pk in Product.all_pks()]


@app.post("/products", response_model=Product)
def createProduct(product: Product):
    return product.save()


@app.get("/products/{pk}", response_model=Product)
def getProductByPk(pk: str):
    return getProduct(pk)


@app.delete("/product/{pk}", response_model=int)
def deleteProduct(pk: str):
    return Product.delete(pk)


def getProduct(pk: str):
    return Product.get(pk)
