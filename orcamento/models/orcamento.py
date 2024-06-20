from odoo import fields, models, api
from odoo.exceptions import ValidationError


class OrcaSale(models.Model):
    _inherit = 'sale.order'

    horas_mo = fields.Integer(string='Total Horas', required=True, compute='_total_horas')
    valor_horas = fields.Monetary(string='Valor Horas', required=True, store=True)
    valor_total_horas = fields.Monetary(string='Valor Total Horas', copy=True, compute='_vtotal_horas')
    valor_total_hmanual = fields.Monetary(string='Valor Horas Manual', store=True)
    # imposto = fields.Many2one('os.impostos.line', string='Imposto %', store=True)
    materia_prima = fields.Monetary(string='Matéria Prima', compute='_total_mp')
    terceiros = fields.Monetary(string='Terceiros', compute='_total_terceiros')
    comissao = fields.Float(string='% Comissão')
    resultado = fields.Monetary(string='Total Sem Imposto', store=False)
    horas_total = fields.Many2many('orca.horas.total', 'horas_total_rel', 'horas_id', 'order_id', string='Horas Previstas')
    order_line_orca = fields.One2many('sale.order.line', 'order_id', string='Order Lines', copy=True)


    def _vtotal_horas(self):

            total = sum(self.order_line_orca.mapped('mo_total')) if self.order_line_orca else 0
            if total:
                self.valor_total_horas = total
            else:
                self.valor_total_horas = self.valor_total_horas

    def _total_horas(self):

            total = sum(self.order_line_orca.mapped('mo')) if self.order_line_orca else 0
            if total:
                self.horas_mo = total
            else:
                self.horas_mo = self.horas_mo

    def _total_terceiros(self):

            total = sum(self.order_line_orca.mapped('terc')) if self.order_line_orca else 0
            if total:
                self.terceiros = total
            else:
                self.terceiros = self.terceiros

    def _total_mp(self):


            total = sum(self.order_line_orca.filtered(lambda l: l.mp > 1).mapped('mp')) if self.order_line_orca else 0

            if total:
                self.materia_prima = total
            else:
                    mp = self.env['sale.order'].browse(self.env.context.get('active_ids')).materia_prima
                    self.materia_prima = mp


    @api.onchange('valor_horas', 'horas_mo')
    def _amount_resultado(self):

        for rec in self:

            if rec.valor_total_hmanual:
                rec.update({'resultado': rec.valor_total_hmanual + rec.materia_prima + rec.terceiros})
            else:
                rec.update({'resultado': rec.valor_total_horas + rec.materia_prima + rec.terceiros})


class OrcaHorasTotal(models.Model):
    _name = 'orca.horas.total'

    funcionario = fields.Many2one('hr.employee', string='Funcionário', store=True, required=True)
    processo = fields.Selection(
        [('corte', 'Corte'), ('dobra', 'Dobra'), ('montagem', 'Montagem'),
         ('solda', 'Solda'), ('acabamento', 'Acabamento'), ('pintura', 'Pintura'), ('embalagem', 'Embalagem')],
        string='Processo', store=True, copy=True, default='corte', required=True)
    htotal = fields.Integer(string='Horas', required=True, store=True)
    dias = fields.Float(string='Dias')
    linha = fields.Many2one('sale.order.line')



# class OrcaHorasPrev(models.TransientModel):
#     _name = 'orca.horas.prev'
#
#     funcionario = fields.Many2one('hr.employee', string='Funcionário', store=True, required=True)
#     processo = fields.Selection(
#         [('corte', 'Corte'), ('dobra', 'Dobra'), ('montagem', 'Montagem'),
#          ('solda', 'Solda'), ('acabamento', 'Acabamento'), ('pintura', 'Pintura'), ('embalagem', 'Embalagem')],
#         string='Processo', store=True, copy=True, default='corte', required=True)
#     htotal = fields.Integer(string='Horas', required=True, store=True)
#     dias = fields.Float(string='Dias')

    # linha = fields.Many2one('sale.order.line', default=lambda self: self.env.context.get('active_id'))

    @api.onchange('htotal')
    def _amount_dias(self):
        for rec in self:
            rec.dias = rec.htotal / 8.8


class OrcaTabela(models.TransientModel):
    _name = "orca.tabela"
    _description = "Tabela de orçamento"

    fiscal = fields.Many2one('account.fiscal.position', string='Posição Fiscal',
                             related='linha.order_id.fiscal_position_id')
    linha = fields.Many2one('sale.order.line', string='Linha Pedido')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)
    mp = fields.Monetary(string='Matéria Prima')
    mo = fields.Integer(string='Horas MO')
    mo_valor = fields.Monetary(string='Valor Hora MO')
    mo_total = fields.Monetary(string='Total Mão de Obra', compute='_amount_horas')
    terc = fields.Monetary(string='Terceiros')
    total = fields.Monetary(string='Total Orçado')
    lucro = fields.Float(string='% Lucro', default=30)
    custos = fields.Float(string='% Custos')

    valor_custo = fields.Monetary(string='Total Custo Fixo', help='Valor proporcional ao custo fixo.')
    valor_venda = fields.Monetary(string='Valor de Venda', compute='calcular')
    valor_serv = fields.Monetary(string='Valor Serviço', compute='calcular')
    valor_ind = fields.Monetary(string='Valor Industrialização', compute='calcular')

    cvenda = fields.Monetary(string='Valor Custo Fixo Venda', help='Valor proporcional da venda ao custo fixo')
    cind = fields.Monetary(string='Valor Custo Fixo Industrialização',
                           help='Valor proporcional da industrialização ao custo fixo')
    cserv = fields.Monetary(string='Valor Custo Fixo Servico', help='Valor proporcional do serviço ao custo fixo')
    # Unrequired company
    produto = fields.Many2one('product.product', string='Produto', related='linha.product_id')
    imposto_venda = fields.Float(string="Imposto Venda %")
    impv_valor = fields.Monetary(string="Imposto Venda $")
    imposto_ind = fields.Float(string="Imposto Industrialização %")
    impi_valor = fields.Monetary(string="Imposto Industrialização $")
    imposto_serv = fields.Float(string="Imposto Serviço %")
    imps_valor = fields.Monetary(string="Imposto Serviço $")

    resulv = fields.Monetary(string="Resultado Venda")
    resuli = fields.Monetary(string="Resultado Industrialização")
    resuls = fields.Monetary(string="Resultado Serviço")

    # horas_prev = fields.One2many('orca.horas.prev', 'funcionario',string='Horas Previstas')

    @api.onchange('mo')
    def _amount_horas(self):
        self.mo_total = self.mo * self.mo_valor

    def default_get(self, fields):

        res = super(OrcaTabela, self).default_get(fields)
        value = self.env['ir.config_parameter'].sudo().get_param('orcamento.custo_fixo')
        vvenda = self.env['ir.config_parameter'].sudo().get_param('orcamento.venda')
        vhora = self.env['ir.config_parameter'].sudo().get_param('orcamento.vhora')
        vservico = self.env['ir.config_parameter'].sudo().get_param('orcamento.servico')
        vindus = self.env['ir.config_parameter'].sudo().get_param('orcamento.industrializacao')
        pedido = self.env.context.get('active_id')
        horas = self.env['sale.order.line'].browse(pedido).mo
        horast = self.env['sale.order.line'].browse(pedido).mo_total
        matp = self.env['sale.order.line'].browse(pedido).mp
        lucro = self.env['sale.order.line'].browse(pedido).lucro
        terc = self.env['sale.order.line'].browse(pedido).terc
        movalor = self.env['sale.order.line'].browse(pedido).mo_valor

        if horas or matp or terc:
            res.update({
                'mp': matp,
                'terc': terc,
                'lucro': lucro,
                'mo_total': horast,
                'custos': value,
                'mo_valor': movalor,
                'imposto_venda': vvenda,
                'imposto_serv': vservico,
                'imposto_ind': vindus,
                'linha': pedido,

            })
        else:
            res.update({
                'custos': value,
                'mo_valor': vhora,
                'imposto_venda': vvenda,
                'imposto_serv': vservico,
                'imposto_ind': vindus,
                'linha': pedido,

            })

        return res

    def salva_select(self):
        self.ensure_one()
        if not self.mo or self.mo == 0:
            raise ValidationError("Insira ao menos 1 hora de trabalho e Valor Hora MO")

        vals = {
            'mp': self.mp,
            'mo': self.mo,
            'mo_valor': self.mo_valor,
            'mo_total': self.mo_total,
            'terc': self.terc,
            'lucro': self.lucro,
            'custos': self.custos,
            'imposto_venda': self.imposto_venda,
            'imposto_ind': self.imposto_ind,
            'imposto_serv': self.imposto_serv,
            'valor_venda': self.valor_venda,
            'valor_serv': self.valor_serv,
            'valor_ind': self.valor_ind,

        }
        record = self.env['sale.order.line'].browse(self.linha.id)

        for rec in record:
            if self.fiscal.name == 'Venda':
                rec.write(vals)
                rec.write({'price_unit': self.valor_venda})

            if self.fiscal.name == 'Industrialização':
                rec.write(vals)
                rec.write({'price_unit': self.valor_ind})

            if self.fiscal.name == 'Serviço':
                rec.write(vals)
                rec.write({'price_unit': self.valor_serv})

    def salva_orca(self):
        self.ensure_one()

        if not self.mo or self.mo == 0:
            raise ValidationError("Insira ao menos 1 hora de trabalho e Valor Hora MO")

        vals = {
            'mp': self.mp,
            'mo': self.mo,
            'mo_valor': self.mo_valor,
            'mo_total': self.mo_total,
            'terc': self.terc,
            'lucro': self.lucro,
            'custos': self.custos,
            'imposto_venda': self.imposto_venda,
            'imposto_ind': self.imposto_ind,
            'imposto_serv': self.imposto_serv,
            'valor_venda': self.valor_venda,
            'valor_serv': self.valor_serv,
            'valor_ind': self.valor_ind,

        }
        record = self.env['sale.order.line'].browse(self.linha.id)


        for rec in record:
            if self.fiscal.name == 'Venda':
                rec.write(vals)

            if self.fiscal.name == 'Industrialização':
                rec.write(vals)


            if self.fiscal.name == 'Serviço':
                rec.write(vals)


    @api.onchange('mp', 'mo', 'mo_valor', 'terc', 'lucro')
    def calcular(self):

        custovenda = (self.custos + self.imposto_venda)
        custoind = (self.custos + self.imposto_ind)
        custoserv = (self.custos + self.imposto_serv)

        indicevenda = custovenda + self.lucro
        indiceind = custoind + self.lucro
        indiceserv = custoserv + self.lucro

        indv = 100 / (100 - indicevenda)
        indi = 100 / (100 - indiceind)
        inds = 100 / (100 - indiceserv)

        self.write({'mo_total': self.mo_valor * self.mo})
        self.write({'total': self.mo_total + self.mp + self.terc})
        self.write({'valor_venda': self.total * indv, 'valor_ind': self.total * indi, 'valor_serv': self.total * inds})

        cv = (self.valor_venda * (self.custos / 100))
        ci = (self.valor_ind * (self.custos / 100))
        cs = (self.valor_serv * (self.custos / 100))

        impv = self.valor_venda / self.imposto_venda
        imps = self.valor_serv / self.imposto_serv
        impi = self.valor_ind / self.imposto_ind

        self.write({'cvenda': cv, 'cind': ci, 'cserv': cs})
        self.write({'impv_valor': impv, 'impi_valor': impi, 'imps_valor': imps})

        resv = (self.valor_venda - cv - impv - self.total)
        resi = (self.valor_ind - ci - impi - self.total)
        ress = (self.valor_serv - cs - imps - self.total)

        self.write({'resulv': resv, 'resuli': resi, 'resuls': ress})


class OrcaGeral(models.Model):

    _inherit = 'sale.order.line'

    mo = fields.Integer(string='Horas MO')
    mo_valor = fields.Monetary(string='Valor Hora MO')
    mo_total = fields.Monetary(string='Total Mão de Obra')

    mp = fields.Monetary(string='Matéria Prima', default=1)
    terc = fields.Monetary(string='Terceiros')

    total = fields.Monetary(string='Total Orçado')
    lucro = fields.Float(string='% Lucro', default=30)
    custos = fields.Float(string='% Custos')

    valor_custo = fields.Monetary(string='Total Custo Fixo', help='Valor proporcional ao custo fixo.')
    valor_venda = fields.Monetary(string='Valor de Venda')
    valor_serv = fields.Monetary(string='Valor Serviço')
    valor_ind = fields.Monetary(string='Valor Industrialização')

    cvenda = fields.Monetary(string='Valor Custo Fixo Venda', help='Valor proporcional da venda ao custo fixo')
    cind = fields.Monetary(string='Valor Custo Fixo Industrialização',
                           help='Valor proporcional da industrialização ao custo fixo')
    cserv = fields.Monetary(string='Valor Custo Fixo Servico', help='Valor proporcional do serviço ao custo fixo')

    imposto_venda = fields.Float(string="Imposto Venda %")
    impv_valor = fields.Monetary(string="Imposto Venda $")
    imposto_ind = fields.Float(string="Imposto Industrialização %")
    impi_valor = fields.Monetary(string="Imposto Industrialização $")
    imposto_serv = fields.Float(string="Imposto Serviço %")
    imps_valor = fields.Monetary(string="Imposto Serviço $")

    resulv = fields.Monetary(string="Resultado Venda")
    resuli = fields.Monetary(string="Resultado Industrialização")
    resuls = fields.Monetary(string="Resultado Serviço")




class OrcaConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)
    custo_fixo = fields.Float(string='Custo Fixo %')
    venda = fields.Float(string='Imposto Venda %')
    servico = fields.Float(string='Imposto Serviço %')
    industrializacao = fields.Float(string='Imposto Industrialização %')
    vhora = fields.Monetary(string='Valor Hora')

    def set_values(self):
        """employee setting field values"""
        res = super(OrcaConfig, self).set_values()
        self.env['ir.config_parameter'].set_param('orcamento.custo_fixo', self.custo_fixo)
        self.env['ir.config_parameter'].set_param('orcamento.vhora', self.vhora)
        self.env['ir.config_parameter'].set_param('orcamento.venda', self.venda)
        self.env['ir.config_parameter'].set_param('orcamento.servico', self.servico)
        self.env['ir.config_parameter'].set_param('orcamento.industrializacao', self.industrializacao)
        return res

    def get_values(self):
        res = super(OrcaConfig, self).get_values()
        value = self.env['ir.config_parameter'].sudo().get_param('orcamento.custo_fixo')
        vhora = self.env['ir.config_parameter'].sudo().get_param('orcamento.vhora')
        vvenda = self.env['ir.config_parameter'].sudo().get_param('orcamento.venda')
        vservico = self.env['ir.config_parameter'].sudo().get_param('orcamento.servico')
        vindus = self.env['ir.config_parameter'].sudo().get_param('orcamento.industrializacao')
        res.update(
            custo_fixo=float(value),
            vhora=vhora,
            venda=float(vvenda),
            servico=float(vservico),
            industrializacao=float(vindus),
        )
        return res


class OrcaImpostos(models.Model):
    _name = "orca.impostos"

    name = fields.Selection([('venda', 'Venda'), ('industrializacao', 'Industrialização'), ('servico', 'Serviço')],
                            string='Tipo', store=True, copy=True, default='venda')
    icms = fields.Float(string='ICMS %')
    ipi = fields.Float(string='IPI %')
    pis = fields.Float(string='PIS %')
    cofins = fields.Float(string='COFINS %')
    ir = fields.Float(string='IR %')
    csl = fields.Float(string='CSL %')
    iss = fields.Float(string='ISS %')
    cpp = fields.Float(string='CPP %')
    total_imp = fields.Float(string='Total %', compute='_total_imp', store=True)

    @api.onchange('pis', 'icms', 'cofins', 'ir', 'csl', 'iss', 'cpp')
    def _total_imp(self):
        for rec in self:
            rec.update({'total_imp': rec.ipi + rec.pis + rec.cofins + rec.ir + rec.csl + rec.iss + rec.cpp + rec.icms})

    # def default_get(self, fields):
    #     res = super(OrcaGeral, self).default_get(fields)
    #     value = self.env['ir.config_parameter'].sudo().get_param('orcamento.custo_fixo')
    #     vvenda = self.env['ir.config_parameter'].sudo().get_param('orcamento.venda')
    #     vhora = self.env['ir.config_parameter'].sudo().get_param('orcamento.vhora')
    #     vservico = self.env['ir.config_parameter'].sudo().get_param('orcamento.servico')
    #     vindus = self.env['ir.config_parameter'].sudo().get_param('orcamento.industrializacao')
    #     pedido = self.env.context.get('active_id')
    #
    #     res.update({
    #         'custos': value,
    #         'mo_valor': vhora,
    #         'imposto_venda': vvenda,
    #         'imposto_serv': vservico,
    #         'imposto_ind': vindus,
    #         'linha': pedido,
    #     })
    #
    #     return res

    # @api.onchange('mp', 'mo', 'mo_valor', 'terc', 'lucro')
    # def calcula(self):
    #     custovenda = (self.custos + self.imposto_venda)
    #     custoind = (self.custos + self.imposto_ind)
    #     custoserv = (self.custos + self.imposto_serv)
    #
    #     indicevenda = custovenda + self.lucro
    #     indiceind = custoind + self.lucro
    #     indiceserv = custoserv + self.lucro
    #
    #     indv = 100 / (100 - indicevenda)
    #     indi = 100 / (100 - indiceind)
    #     inds = 100 / (100 - indiceserv)
    #
    #     self.write({'mo_total': self.mo_valor * self.mo})
    #     self.write({'total': self.mo_total + self.mp + self.terc})
    #     self.write({'valor_venda': self.total * indv, 'valor_ind': self.total * indi, 'valor_serv': self.total * inds})
    #
    #     cv = (self.valor_venda * (self.custos / 100))
    #     ci = (self.valor_ind * (self.custos / 100))
    #     cs = (self.valor_serv * (self.custos / 100))
    #
    #     impv = self.valor_venda / self.imposto_venda
    #     imps = self.valor_serv / self.imposto_serv
    #     impi = self.valor_ind / self.imposto_ind
    #
    #     self.write({'cvenda': cv, 'cind': ci, 'cserv': cs})
    #     self.write({'impv_valor': impv, 'impi_valor': impi, 'imps_valor': imps})
    #
    #     resv = (self.valor_venda - cv - impv - self.total)
    #     resi = (self.valor_ind - ci - impi - self.total)
    #     ress = (self.valor_serv - cs - imps - self.total)
    #
    #     self.write({'resulv': resv, 'resuli': resi, 'resuls': ress})

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', ('New')) == ('New'):
    #         vals['name'] = self.env['ir.sequence'].next_by_code('orca.seq') or ('New')
    #         result = super(OrcaGeral, self).create(vals)
    #
    #         return result
