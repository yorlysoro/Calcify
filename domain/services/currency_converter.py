# BSD 3-Clause License
#
# Copyright (c) 2026, yorlysoro
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from decimal import Decimal, ROUND_HALF_UP

from domain.exceptions import InvalidExchangeRateError


class CurrencyConverter:
    """
    A stateless domain service for currency conversion using Decimal math.

    Converts monetary amounts through the main/base currency using pre-calculated
    inverse exchange rates. Formula: (amount * target_inverse) / source_inverse

    This ensures all conversions flow through the main currency:
      1. Convert source to main:  amount / source_inverse = amount * source_rate
      2. Convert main to target:  (amount in main) * target_inverse
      3. Combined: amount * target_inverse / source_inverse
    """

    @staticmethod
    def convert(
        amount: Decimal,
        source_inverse: Decimal,
        target_inverse: Decimal,
    ) -> Decimal:
        """
        Converts an amount using source and target inverse exchange rates.

        Always routes through the main/base currency for precision.

        Formula: (amount * target_inverse) / source_inverse

        Args:
            amount (Decimal): The monetary value to convert.
            source_inverse (Decimal): Inverse rate of the source currency (1/rate).
                                      Pass Decimal("1") if source is the main currency.
            target_inverse (Decimal): Inverse rate of the target currency (1/rate).
                                      Pass Decimal("1") if target is the main currency.

        Returns:
            Decimal: The converted amount rounded to 4 decimal places.

        Raises:
            InvalidExchangeRateError: If either inverse rate is zero.
        """
        src_inv: Decimal = Decimal(str(source_inverse))
        tgt_inv: Decimal = Decimal(str(target_inverse))

        if src_inv == Decimal("0") or tgt_inv == Decimal("0"):
            raise InvalidExchangeRateError("Exchange rate cannot be zero.")

        result: Decimal = (amount * tgt_inv) / src_inv
        return result.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
