from seller.models import Product, ProductImage

def header_products(request):
    try:
        products = []
        for product in Product.objects.all():
            # Get the first image for this product
            first_image = ProductImage.objects.filter(product=product).first()
            image_url = first_image.image.url if first_image else '/static/images/default-product.png'
            
            products.append({
                'id': product.id,
                'name': product.name,
                'brand': product.brand,
                'price': product.price,
                'image_url': image_url
            })
        
        return {
            'header_products': products
        }
    except:
        return {
            'header_products': []
        }