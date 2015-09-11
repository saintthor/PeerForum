var Forum = function( owner )
{
	var frm = this;

	this.Owner = owner;

	this.Init = function()
	{
		$( '#newtpcbtn' ).click( function()
		{
			//alert( 'ssssss' );
			$( '#tpcinput' ).toggle( 350 );
		} );

		$( '#tpctd>button' ).click( function()
		{
			//console.log( 'newtopic' );
			var Content = $( '#tpctd>textarea' ).val()
			if( Content.length < 20 )
			{
				$( '#tpctd>.note' ).html( '帖子内容不能少于 20 字。' );
				return;
			}

			var AtclLabels = $( '#tpctd>:text' ).val()

			//console.log( AtclLabels );
			if( !AtclLabels )
			{
				$( '#tpctd>.note' ).html( '标签不能为空。' );
				return;
			}

			$( '#tpctd>.note' ).html( '' );

			var TopicData = {
				'cmd': 'NewTopic',
				'content': Content,
				'Labels': AtclLabels,
				'life': 86400000 * $( '#tpctd>select' ).children( 'option:selected' ).val(),
			};

			console.log( TopicData );

			frm.Owner.Post( TopicData, 'GetResult' );
		} );
	};

	this.ShowTime = function( intTime )
	{
		var d = new Date();
		d.setTime( intTime );
		return d.getFullYear() + '-' + ( d.getMonth() + 1 ) + '-' + d.getDate() + ' '
				+ d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds();
	};

	this.TopicTR = function( tpcdata )
	{
		var TR = $( '<tr><td class="title"></td><td class="first"></td><td class="num">1</td><td class="last"></td></tr>' );
		var LabelSpans = _( tpcdata[2].split( ',' )).chain().map( function( lb )
			{
				return '<span class="tpclabel">' + lb + '</span>';
			} ).value().join( '' );
		console.log( LabelSpans );
		var Title = '<span class="arrow">◣</span><span class="title">' + tpcdata[1] + '</span>' + LabelSpans;
		TR.children( 'td:eq(0)' ).html( Title )
		TR.children( 'td:eq(1)' ).html( tpcdata[5] + '<br>' + this.ShowTime( tpcdata[6] ));
		TR.children( 'td:eq(2)' ).html( tpcdata[4] )
		TR.children( 'td:eq(3)' ).html( '<span class="last">' + this.ShowTime( tpcdata[8] ) + '</span><br>' + tpcdata[7] );
		TR.data( 'root', tpcdata[0] );

		return TR;
	};

	this.Init();
}