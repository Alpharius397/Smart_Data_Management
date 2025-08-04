from pyhanko import stamp
from pyhanko.pdf_utils import images, text
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers
from asgiref.sync import sync_to_async
import io

from User.models import User

SIGNER = signers.SimpleSigner.load(
    'Signature/key.pem', 'Signature/cert.pem',
)

def signature_header(user: User):
    return f"Signed By: {user.username}\nUniversity: {user.role.belongs.institute.university.name}\nInstitute: {user.role.belongs.institute.name}\nBranch: {user.role.belongs.name}\nTimestamp: %(ts)s"
    

async def addSign(input: io.BytesIO, signer: User):
    
    w = IncrementalPdfFileWriter(input)
    fields.append_signature_field(
        w, sig_field_spec=fields.SigFieldSpec(
            'Signature', on_page=-1, box=(480, 10, 580, 70), 
        )
    )
    
    meta = signers.PdfSignatureMetadata(field_name='Signature')
    pdf_signer = signers.PdfSigner(
        meta, signer=SIGNER, stamp_style=stamp.TextStampStyle(
            border_width=1,
            stamp_text=(await sync_to_async(signature_header)(signer)),
            background=images.PdfImage('static/images/stamp.jpg'),
        )
    )
    
    return await pdf_signer.async_sign_pdf(w)