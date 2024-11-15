from odoo import models, fields

class MajestyDocuments(models.Model):
    _name = 'commercial.documents'
    _description = 'Majesty Documents'

    # Field for uploading the document (binary)
    document_binary = fields.Binary( required=True)

    # Field for storing the document name (char)
    document_name = fields.Char(required=True)

    # Many-to-one relationship: Each document is related to one project
    project_id = fields.Many2one('commercial.project', string='Project')
    desginer_id = fields.Many2one('designer.project', string='Project')
