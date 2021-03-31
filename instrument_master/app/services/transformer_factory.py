"""
Produce transformer objects.

Import as: import instrument_master.app.services.transformer_factory as vastra
"""
import instrument_master.common.data.transform.s3_to_sql_transformer as vcdts3
import instrument_master.kibot.data.transform.s3_to_sql_transformer as vkdts3


class TransformerFactory:
    @classmethod
    def get_s3_to_sql_transformer(
        cls, provider: str
    ) -> vcdts3.AbstractS3ToSqlTransformer:
        """
        Get s3 data to sql data transformer for provider.

        :param provider: provider (kibot, ...)
        :raises ValueError: if s3-to-sql transformer is not implemented for provider
        """
        transformer: vcdts3.AbstractS3ToSqlTransformer
        if provider == "kibot":
            transformer = vkdts3.S3ToSqlTransformer()
        else:
            raise ValueError(
                "S3 to SQL transformer for %s is not implemented" % provider
            )
        return transformer