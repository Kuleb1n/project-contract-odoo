from odoo import fields, models


class EditNameContract(models.TransientModel):
    _name = "edit.name.contract"
    _description = "Editing the contract name"

    new_name = fields.Char(string="New contract name")

    def update_contract_name(self):
        """
        Contract name update method
        """

        contract_id = self.env.context.get("contract_id")
        contract = self.env["contract.contract"].browse(contract_id)
        contract.name = self.new_name
        return contract
