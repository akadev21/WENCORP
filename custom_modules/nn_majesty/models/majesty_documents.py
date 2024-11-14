from odoo import models, fields

class MajestyDocuments(models.Model):
    _name = 'majesty.documents'
    _description = 'Majesty Documents'

    # Field for uploading the document (binary)
    document_binary = fields.Binary(string="Document", required=True)

    # Field for storing the document name (char)
    document_name = fields.Char(string="Document Name", required=True)

    # Many-to-one relationship: Each document is related to one project
    project_id = fields.Many2one('majesty.project', string='Project', required=True)
