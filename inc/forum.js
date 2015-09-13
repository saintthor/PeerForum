var Forum = function( owner )
{
	var frm = this;

	this.Owner = owner;
	this.StartPos = 0;
	this.ListLabel = '';
	this.SortCol = 'LastTime';
	this.TopicObj = {};


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

		$( '#firstth' ).click( function()
		{
			frm.SortCol = 'FirstTime';
			frm.StartPos = 0;
			$( '#lastth>span' ).prependTo( $( this ));

			frm.GetNextPage();
		} );

		$( '#lastth' ).click( function()
		{
			frm.SortCol = 'LastTime';
			frm.StartPos = 0;
			$( '#firstth>span' ).prependTo( $( this ));

			frm.GetNextPage();
		} );

		$( '#returntolist' ).click( function()
		{
			$( '#atclpg' ).hide( 200 );
			$( '#forumpg' ).show( 300 );
		} );
	};

	this.SetClickTitle = function( dom )
	{
		$( 'span.title', dom ).click( function()
		{
			var Root = $( this ).closest( 'tr' ).data( 'root' );
			console.log( Root );
			frm.Owner.Post( { cmd: 'GetAtclTree', root: Root }, 'GetResult' );
		} );
	};

	this.SetClickLastTime = function( dom )
	{

	};
	
	this.SetClickArrow = function( dom )
	{

	};

	this.SetAttr = function( dom )
	{
		this.SetClickTitle( dom );
		this.SetClickLastTime( dom );
		this.SetClickArrow( dom );

		setTimeout( function(){ dom.removeClass( 'new' ); }, 2000 );
	};
	
	this.ShowContent = function( c )
	{
		return c.replace( /\&/g, '&amp;' ).replace( /\>/g, '&gt;' ).replace( /\</g, '&lt;' ).replace( /\n/g, '<br/>' );
	};

	this.ShowAtcls = function( treeData )
	{
		this.TopicObj[treeData[0]] = treeData[1];

		$( '#atclarea' ).html( '' );
		
		_( treeData[1] ).chain().pairs().sortBy( function( p )
		{
			return p[1][0].CreateTime;
		} ).each( function( p )
		{
			var AtclDiv = $( '<div class="atcl" id="Atcl_' + p[0] + '"><table><tbody><tr> \
				<td class="atclleft"><div class="nickname"></div><div class="randomart"></div> \
				<div class="manageuser"></div></td><td><div class="atcltop"></div><div class="atclbody"></div> \
				<div class="atclfoot"></div></td></tr></tbody></table><div></div></div>' );

			$( '.nickname', AtclDiv ).html( p[1][0].NickName );
			$( '.atclbody', AtclDiv ).html( frm.ShowContent( p[1][1] ));
			//$( '.randomart', AtclDiv ).html( frm.RandomArt( [62, 25, 88, 1, 40, 77, 37, 98, 51, 29, 8, 16, 20, 26, 70, 8] ));
			$( '.randomart', AtclDiv ).html( frm.RandomArt( str_md5( p[1][0].AuthPubKey )));
			$( '#atclarea' ).append( AtclDiv );
		} );
	};

	this.RandomArt = function( data )
	{
		var Bound = [
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
					];

		var x = 8;
		var y = 4;

		Bound[y][x] = -1;

		_( data ).each( function( c )
		{
			var Byte = c.charCodeAt();
			for( var i = 0; i < 4; i++ )
			{
				if( Byte & 0x01 )
				{
					if( x < 16 )
					{
						x++;
					}
				}
				else
				{
					if( x > 0 )
					{
						x--;
					}
				}

				if( Byte & 0x02 )
				{
					if( y < 8 )
					{
						y++;
					}
				}
				else
				{
					if( y > 0 )
					{
						y--;
					}
				}

				if( Bound[y][x] >= 0 )
				{
					Bound[y][x]++;
				}
				
				Byte >>= 2;
			}
		} );

		Bound[y][x] = -2;

		var s = '';
		_( Bound ).each( function( ln )
		{
			_( ln ).each( function( n )
			{
				s += n >= 0 ? ' .o+=*BOX@%&#/^ES'[n] : 'ES'[n + 2];
			} );
			s += '<br/>'
		} );

		return s.replace( / /g, '&nbsp;' );
	};

	this.GetNextPage = function()
	{
		var Param = {
			'cmd': 'GetTpcList',
			'start': this.StartPos,
			'label': this.ListLabel,
			'sortby': this.SortCol,
					};
		console.log( Param );

		if( this.StartPos == 0 )
		{
			$( '#tpclist>table>tbody>tr:gt(0)' ).remove();
		}

		frm.Owner.Post( Param, 'GetResult' );
	};

	this.FillZero = function( s )
	{
		return ( '00' + s ).slice( -2 );
	};

	this.ShowTime = function( intTime, onlyDate )
	{
		var d = new Date();
		d.setTime( intTime );
		if( onlyDate )
		{
			return d.getFullYear() + '-' + this.FillZero( d.getMonth() + 1 ) + '-' + this.FillZero( d.getDate());
		}
		return d.getFullYear() + '-' + this.FillZero( d.getMonth() + 1 ) + '-' + this.FillZero( d.getDate()) + ' '
				+ this.FillZero( d.getHours()) + ':' + this.FillZero( d.getMinutes()) + ':' + this.FillZero( d.getSeconds());
	};

	this.TopicTR = function( tpcdata )
	{
		var TR = $( '<tr class="new" title="展开话题"><td class="title" title="进入话题"></td> \
			<td class="first"></td><td class="num">1</td><td class="last" title="查看更新"></td></tr>' );
		var LabelSpans = _( tpcdata[2].split( ',' )).chain().map( function( lb )
			{
				return '<span class="tpclabel">' + lb + '</span>';
			} ).value().join( '' );
		//console.log( LabelSpans );
		var Title = '<span class="arrow">◣</span><span class="title">' + tpcdata[1] + '</span>' + LabelSpans;
		TR.children( 'td:eq(0)' ).html( Title )
		TR.children( 'td:eq(1)' ).html( tpcdata[5] + '<br><span class="firsttime">' + this.ShowTime( tpcdata[6], true ) + '</span>' );
		TR.children( 'td:eq(2)' ).html( tpcdata[4] )
		TR.children( 'td:eq(3)' ).html( '<span class="lasttime">' + this.ShowTime( tpcdata[8] ) + '</span><br>' + tpcdata[7] );
		TR.data( 'root', tpcdata[0] );
console.log( tpcdata[0] );
		return TR;
	};

	this.Init();
}